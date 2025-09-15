import json
import random

from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.account.services import AccountService
from apps.enums import FollowerChangeStatusEnum
from .serializers import FollowingSerializer, FollowerSerializer, ProfileSerializer
from .models import FollowerChange


class ProfileConfig:
    update_follow_task = "analyze_follow_data_user_{account_id}"
    growth_data_task = "analyze_account_growth_logs_{account_id}"

    def create_analyze_growth_logs_periodic_task(self, account_id:int):
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

    def create_analyze_update_follow_data_periodic_task(self, account_id:int):
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

    def pause_or_resume_analyze_update_follow_data_periodic_task(self, account_id:int, pause: bool):
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

    def reschedule_analyze_update_follow_data_periodic_task(self, account_id:int):
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
    def load_profile_info(account, client):
        data = client.user_info(str(account.client_pk), use_cache=False).dict()
        data["account"] = account.pk
        data["user_pk"] = int(data["pk"])
        data["profile_pic_url"] = str(data["profile_pic_url"])
        return data

    @staticmethod
    def load_followers(account, client) -> list[dict]:
        followers = client.user_followers(str(account.client_pk), use_cache=False).values()
        data = [{
            "account": account.pk,
            "user_pk": int(follower.pk),
            "username": follower.username,
            "full_name": follower.full_name,
            "profile_pic_url": str(follower.profile_pic_url),
        } for follower in followers
        ]
        return data

    @staticmethod
    def load_followings(account, client) -> list[dict]:
        followings = client.user_following(str(account.client_pk), use_cache=False).values()
        data = [{
            "account": account.pk,
            "user_pk": int(follower.pk),
            "username": follower.username,
            "full_name": follower.full_name,
            "profile_pic_url": str(follower.profile_pic_url),
        } for follower in followings
        ]
        return data

    def fetch_profile_info(self, account, client):
        profile_info = self.load_profile_info(account, client)
        serializer = ProfileSerializer(data=profile_info)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def fetch_followers(self, account, client) -> list[dict]:
        data = self.load_followers(account, client)
        serializer = FollowerSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return data

    def fetch_followings(self, account, client) -> list[dict]:
        data = self.load_followings(account, client)
        serializer = FollowingSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return data

    def analyze_follower_changes(self, account, followers: list[dict], followings: list[dict]) -> None:
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
