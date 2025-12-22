import json
import random

from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.enums import FollowerChangeStatusEnum
from apps.core.utils.instagram_client import InstagramBaseClient
from .serializers import ProfileSerializer
from .models import FollowerChange, Follower, Following, Post
from ..core.utils.instagram_client.exceptions import exception_mapper


class ProfileConfig:
    update_follow_task_name = "analyze_follow_data_user_{account_id}"

    @staticmethod
    def extract_account_id(task_name: str) -> int | None:
        return int(task_name.split("_")[-1])

    def create_analyze_update_follow_data_periodic_task(self, account_id: int):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )
        task_name_ = self.update_follow_task_name.format(account_id=account_id)
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
            task = PeriodicTask.objects.get(name=self.update_follow_task_name.format(account_id=account_id))
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
            task = PeriodicTask.objects.get(name=self.update_follow_task_name.format(account_id=account_id))
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
    config = ProfileConfig()
    batch_size = 1000

    @staticmethod
    def load_profile_info(account, client: InstagramBaseClient):
        try:
            return client.load_profile(account=account)
        except Exception as exc:
            exception_mapper(exc)

    @staticmethod
    def load_followers(account, client: InstagramBaseClient):
        try:
            for users in client.load_followers_in_chunk(account=account):
                yield users
        except Exception as exc:
            exception_mapper(exc)

    @staticmethod
    def load_followings(account, client: InstagramBaseClient):
        try:
            for users in client.load_followings_in_chunk(account=account):
                yield users
        except Exception as exc:
            exception_mapper(exc)

    @staticmethod
    def load_user_posts(account, client: InstagramBaseClient):
        try:
            for medias in client.get_user_posts_in_chunk():
                yield medias
        except Exception as exc:
            exception_mapper(exc)

    def fetch_profile_info(self, account, client: InstagramBaseClient) -> None:
        profile_info = self.load_profile_info(account, client)
        serializer = ProfileSerializer(data=profile_info)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def fetch_followers(self, account, client: InstagramBaseClient) -> None:
        for chunk in self.load_followers(account, client):
            objs = [Follower(account=account, **item) for item in chunk]
            Follower.objects.bulk_create(objs, batch_size=self.batch_size)

    def fetch_followings(self, account, client: InstagramBaseClient) -> None:
        for chunk in self.load_followings(account, client):
            objs = [Following(account=account, **item) for item in chunk]
            Following.objects.bulk_create(objs, batch_size=self.batch_size)

    def fetch_medias(self, account, client: InstagramBaseClient) -> None:
        for chunk in self.load_user_posts(account, client):
            objs = [Post(account=account, **item) for item in chunk]
            Post.objects.bulk_create(objs, batch_size=self.batch_size)

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
