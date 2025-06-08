import json

from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.account.services import AccountService
from apps.enums import FollowerChangeStatusEnum
from .serializers import FollowingSerializer, FollowerSerializer, ProfileSerializer
from .models import FollowerChange


class ProfileConfig:
    task_expire_time = 3600  # 1 hour
    update_follow_task = "analyze_follow_data_user_{account_id}"
    growth_data_task = "analyze_account_growth_logs_{account_id}"

    def create_analyze_growth_logs_periodic_task(self, account_id):
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
                expires=self.task_expire_time,
                start_time=timezone.now()
            )

    def delete_analyze_growth_logs_periodic_task(self, account_id):
        try:
            task = PeriodicTask.objects.get(nama=self.growth_data_task.format(account_id=account_id))
        except PeriodicTask.DoesNotExist:
            pass
        else:
            task.delete()

    def create_analyze_update_follow_data_periodic_task(self, account_id):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=3,
            period=IntervalSchedule.HOURS,
        )
        task_name_ = self.update_follow_task.format(account_id=account_id)
        if not PeriodicTask.objects.filter(name=task_name_).exists():
            PeriodicTask.objects.create(
                interval=schedule,
                name=task_name_,
                task="apps.profiles.tasks.analyze_and_update_follow_data",
                args=json.dumps([account_id]),
                enabled=True,
                expires=self.task_expire_time
            )

    def delete_analyze_update_follow_data_periodic_task(self, account_id):
        try:
            task = PeriodicTask.objects.get(name=self.update_follow_task.format(account_id=account_id))
        except PeriodicTask.DoesNotExist:
            pass
        else:
            task.delete()


class ProfileService:
    account_svc = AccountService()
    config = ProfileConfig()
    batch_size = 1000

    def load_profile_info(self, account):
        self.account_svc.client.set_settings(json.loads(account.client_settings))
        data = self.account_svc.client.user_info(account.client_pk).dict()
        data["account"] = account.pk
        data["user_pk"] = int(data["pk"])
        data["profile_pic_url"] = str(data["profile_pic_url"])
        return data

    def load_followers(self, account) -> list[dict]:
        self.account_svc.client.set_settings(json.loads(account.client_settings))
        followers = self.account_svc.client.user_followers(str(account.client_pk)).values()
        data = [{
            "account": account.pk,
            "user_pk": follower.pk,
            "username": follower.username,
            "full_name": follower.full_name,
            "profile_pic_url": str(follower.profile_pic_url),
        } for follower in followers
        ]
        return data

    def load_followings(self, account) -> list[dict]:
        self.account_svc.client.set_settings(json.loads(account.client_settings))
        followings = self.account_svc.client.user_following(str(account.client_pk)).values()
        data = [{
            "account": account.pk,
            "user_pk": follower.pk,
            "username": follower.username,
            "full_name": follower.full_name,
            "profile_pic_url": str(follower.profile_pic_url),
        } for follower in followings
        ]
        return data

    def fetch_profile_info(self, account):
        profile_info = self.load_profile_info(account)
        print(profile_info)
        serializer = ProfileSerializer(data=profile_info)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def fetch_followers(self, account) -> list[dict]:
        data = self.load_followers(account)
        serializer = FollowerSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return data

    def fetch_followings(self, account) -> list[dict]:
        data = self.load_followings(account)
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
