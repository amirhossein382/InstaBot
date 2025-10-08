import json
import random

from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.account.services import AccountService
from apps.enums import FollowerChangeStatusEnum
from .serializers import ProfileSerializer
from .models import FollowerChange, Follower, Following


class ProfileConfig:
    update_follow_task = "analyze_follow_data_user_{account_id}"
    growth_data_task = "analyze_account_growth_logs_{account_id}"

    @staticmethod
    def extract_account_id(task_name: str) -> int | None:
        return int(task_name.split("_")[-1])

    def create_analyze_growth_logs_periodic_task(self, account_id: int):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )
        task_name_ = self.growth_data_task.format(account_id=account_id)
        if not PeriodicTask.objects.filter(name=task_name_).exists():
            PeriodicTask.objects.create(
                interval=schedule,
                name=task_name_,
                task="apps.profiles.tasks.analyze_account_growth_logs",
                args=json.dumps([account_id]),
                enabled=True,
                one_off=False,
                start_time=timezone.now()
            )

    def pause_or_resume_analyze_growth_logs_periodic_task(self, account_id: int, pause: bool):
        try:
            task = PeriodicTask.objects.get(name=self.growth_data_task.format(account_id=account_id))
        except PeriodicTask.DoesNotExist:
            pass
        else:
            if pause:
                task.enabled = False
            else:
                task.enabled = True
            task.save()

    def create_analyze_update_follow_data_periodic_task(self, account_id: int):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )
        task_name_ = self.update_follow_task.format(account_id=account_id)
        if not PeriodicTask.objects.filter(name=task_name_).exists():
            PeriodicTask.objects.create(
                interval=schedule,
                name=task_name_,
                task="apps.profiles.tasks.analyze_and_update_follow_data",
                args=json.dumps([account_id]),
                one_off=False,
                enabled=True,
            )

    def pause_or_resume_analyze_update_follow_data_periodic_task(self, account_id: int, pause: bool):
        try:
            task = PeriodicTask.objects.get(name=self.update_follow_task.format(account_id=account_id))
        except PeriodicTask.DoesNotExist:
            pass
        else:
            if pause:
                task.enabled = False
            else:
                task.enabled = True
            task.save()

    def reschedule_analyze_update_follow_data_periodic_task(self, account_id: int):
        try:
            task = PeriodicTask.objects.get(name=self.update_follow_task.format(account_id=account_id))
        except PeriodicTask.DoesNotExist:
            pass
        else:
            next_run_time = random.randint(5, 20)
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=next_run_time,
                period=IntervalSchedule.MINUTES,
            )
            task.interval = schedule
            task.save()
            return next_run_time


class ProfileService:
    account_svc = AccountService()
    config = ProfileConfig()
    batch_size = 1000

    @staticmethod
    def _clean_user_object(user):
        return {
            "user_pk": int(user.pk),
            "username": user.username,
            "full_name": user.full_name,
            "profile_pic_url": str(user.profile_pic_url),
        }

    @staticmethod
    def load_profile_info(account, client):
        data = client.user_info(str(account.client_pk), use_cache=False).dict()
        data["account"] = account.pk
        data["user_pk"] = int(data["pk"])
        data["profile_pic_url"] = str(data["profile_pic_url"])
        return data

    def load_followers(self, account, client):
        max_id = ""
        max_amount = 200
        buffer = []
        while True:
            users, max_id = client.user_followers_v1_chunk(
                user_id=str(account.client_pk), max_amount=max_amount, max_id=max_id
            )
            for user in users:
                buffer.append(self._clean_user_object(user))
                if len(buffer) >= batch_size:
                    yield buffer
                    buffer.clear()
            if not max_id:
                break

        if buffer:
            yield buffer

    def load_followings(self, account, client):
        max_id = ""
        max_amount = 200
        buffer = []
        while True:
            users, max_id = client.user_following_v1_chunk(
                user_id=str(account.client_pk), max_amount=max_amount, max_id=max_id
            )
            for user in users:
                buffer.append(self._clean_user_object(user))
                if len(buffer) >= batch_size:
                    yield buffer
                    buffer.clear()
            if not max_id:
                break

        if buffer:
            yield buffer

    def fetch_profile_info(self, account, client) -> None:
        profile_info = self.load_profile_info(account, client)
        serializer = ProfileSerializer(data=profile_info)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def fetch_followers(self, account, client) -> None:
        for chunk in self.load_followers(account, client):
            objs = [Follower(account=account, **item) for item in chunk]
            Follower.objects.bulk_create(objs, batch_size=1000)

    def fetch_followings(self, account, client) -> None:
        for chunk in self.load_followings(account, client):
            objs = [Following(account=account, **item) for item in chunk]
            Following.objects.bulk_create(objs, batch_size=1000)

    def analyze_follower_changes(self, account) -> None:
        followers = Follower.objects.filter(account=account).values(
            "user_pk", "username", "full_name", "profile_pic_url"
        ).iterator()
        followings = Following.objects.filter(account=account).values(
            "user_pk", "username", "full_name", "profile_pic_url"
        ).iterator()
        follower_map: dict = {f["user_pk"]: f for f in followers}
        following_map: dict = {f["user_pk"]: f for f in followings}

        follower_pks = set(follower_map.keys())
        following_pks = set(following_map.keys())

        mutuals_set = follower_pks.intersection(following_pks)
        not_back_set = following_pks - follower_pks

        change_objects = []

        # Mutual Followers
        for pk in mutuals_set:
            f = follower_map[pk]
            change_objects.append(FollowerChange(
                account=account,
                user_pk=pk,
                username=f["username"],
                full_name=f["full_name"],
                profile_pic_url=f["profile_pic_url"],
                change_type=FollowerChangeStatusEnum.MUTUAL
            ))

        # NotBack Followers
        for pk in not_back_set:
            f = following_map[pk]
            change_objects.append(FollowerChange(
                account=account,
                user_pk=pk,
                username=f["username"],
                full_name=f["full_name"],
                profile_pic_url=f["profile_pic_url"],
                change_type=FollowerChangeStatusEnum.NOT_BACK
            ))

        FollowerChange.objects.bulk_create(change_objects, batch_size=self.batch_size)

    def unfollow_user(self, account, user_pk):
        client = self.account_svc.config.get_account_client(account)
        return client.user_unfollow(str(user_pk))
