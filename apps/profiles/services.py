import json

from apps.account.services import AccountService
from apps.enums import FollowerChangeStatusEnum
from .serializers import FollowingSerializer, FollowerSerializer, ProfileSerializer
from .models import FollowerChange


class ProfileService:
    account_svc = AccountService()

    def load_profile_info(self, user):
        self.account_svc.client.set_settings(json.loads(user.client_settings))
        data = self.account_svc.client.user_info(self.account_svc.client.user_id).dict()
        data["user"] = user.pk
        data["user_pk"] = int(data["pk"])
        data["profile_pic_url"] = str(data["profile_pic_url"])
        return data

    def load_followers(self, user) -> list[dict]:
        self.account_svc.client.set_settings(json.loads(user.client_settings))
        followers = self.account_svc.client.user_followers(str(self.account_svc.client.user_id)).values()
        data = [{
            "user": user.pk,
            "user_pk": follower.pk,
            "username": follower.username,
            "full_name": follower.full_name,
            "profile_pic_url": str(follower.profile_pic_url),
        } for follower in followers
        ]
        return data

    def load_followings(self, user) -> list[dict]:
        self.account_svc.client.set_settings(json.loads(user.client_settings))
        followings = self.account_svc.client.user_following(str(self.account_svc.client.user_id)).values()
        data = [{
            "user": user.pk,
            "user_pk": follower.pk,
            "username": follower.username,
            "full_name": follower.full_name,
            "profile_pic_url": str(follower.profile_pic_url),
        } for follower in followings
        ]
        return data

    def fetch_profile_info(self, user):
        profile_info = self.load_profile_info(user)
        print(profile_info)
        serializer = ProfileSerializer(data=profile_info)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def fetch_followers(self, user) -> list[dict]:
        data = self.load_followers(user)
        serializer = FollowerSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return data

    def fetch_followings(self, user) -> list[dict]:
        data = self.load_followings(user)
        serializer = FollowingSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return data

    def analyze_follower_changes(self, user, followers: list[dict], followings: list[dict]) -> None:
        follower_map: dict = {f["user_pk"]: f for f in followers}
        following_map: dict = {f["user_pk"]: f for f in followings}

        follower_pks = set(follower_map.keys())
        following_pks = set(following_map.keys())

        mutuals = follower_pks.intersection(following_pks)
        not_back = following_pks - follower_pks

        change_objects = []

        # Mutual Followers
        for pk in mutuals:
            f = follower_map[pk]
            change_objects.append(FollowerChange(
                user=user,
                user_pk=pk,
                username=f["username"],
                full_name=f["full_name"],
                profile_pic_url=f["profile_pic_url"],
                change_type=FollowerChangeStatusEnum.MUTUAL
            ))

        # NotBack Followers
        for pk in not_back:
            f = following_map[pk]
            change_objects.append(FollowerChange(
                user=user,
                user_pk=pk,
                username=f["username"],
                full_name=f["full_name"],
                profile_pic_url=f["profile_pic_url"],
                change_type=FollowerChangeStatusEnum.NOT_BACK
            ))

        FollowerChange.objects.bulk_create(change_objects, batch_size=1000)
