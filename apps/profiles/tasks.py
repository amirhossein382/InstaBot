from django.db.models import Q
from django.db import transaction
from django.contrib.auth import get_user_model
from celery import shared_task

from apps.enums import FollowerChangeStatusEnum
from .models import Follower, Following, FollowerChange, Profile
from .serializers import ProfileSerializer
from .services import ProfileService

profile_svc = ProfileService()


@shared_task
def analyze_and_update_follow_data(user_id):
    user = get_user_model().objects.get(pk=user_id)
    new_profile_info = profile_svc.load_profile_info(user)
    new_followers = profile_svc.load_followers(user)
    new_followings = profile_svc.load_followings(user)

    new_followers_dict = {item["user_pk"]: item for item in new_followers}
    new_followings_dict = {item["user_pk"]: item for item in new_followings}

    old_profile_info = Profile.objects.get(user=user)
    old_followers = Follower.objects.filter(user=user)
    old_followings = Following.objects.filter(user=user)

    old_followers_dict = {f.user_pk: f for f in old_followers}
    old_followings_dict = {f.user_pk: f for f in old_followings}

    old_follower_pks = set(old_followers_dict.keys())
    old_following_pks = set(old_followings_dict.keys())
    new_follower_pks = set(new_followers_dict.keys())
    new_following_pks = set(new_followings_dict.keys())

    new_followers_set = new_follower_pks - old_follower_pks
    unfollowers_set = old_follower_pks - new_follower_pks

    new_followings_set = new_following_pks - old_following_pks
    unfollowings_set = old_following_pks - new_following_pks

    mutual_set = new_follower_pks.intersection(new_following_pks)
    not_back_set = new_following_pks - new_follower_pks

    changes = []

    def build_change(user_pk, change_type, source_dict):
        data = source_dict[user_pk]
        return FollowerChange(
            user=user,
            user_pk=user_pk,
            change_type=change_type,
            username=data.get("username"),
            full_name=data.get("full_name", None),
            profile_pic_url=data.get("profile_pic_url", None),
        )

    for pk in new_followers_set:
        changes.append(build_change(pk, FollowerChangeStatusEnum.NEW_FOLLOW, new_followers_dict))
    for pk in unfollowers_set:
        changes.append(build_change(pk, FollowerChangeStatusEnum.UNFOLLOW, old_followers_dict))
    for pk in mutual_set:
        changes.append(build_change(pk, FollowerChangeStatusEnum.MUTUAL, new_followers_dict))
    for pk in not_back_set:
        changes.append(build_change(pk, FollowerChangeStatusEnum.NOT_BACK, new_followings_dict))

    with transaction.atomic():
        # Update profile...
        serializer = ProfileSerializer(instance=old_profile_info, data=new_profile_info)
        if serializer.is_valid():
            serializer.save()

        # Delete expired Changes...
        FollowerChange.objects.filter(
            Q(user_pk__in=unfollowers_set) | Q(user_pk__in=unfollowings_set),
            user=user,
            change_type=FollowerChangeStatusEnum.MUTUAL,
        ).delete()
        FollowerChange.objects.filter(
            Q(user_pk__in=unfollowings_set) | Q(user_pk__in=new_followers_set),
            user=user,
            change_type=FollowerChangeStatusEnum.NOT_BACK,
        ).delete()
        FollowerChange.objects.filter(
            change_type=FollowerChangeStatusEnum.NEW_FOLLOW,
            user=user,
            user_pk__in=unfollowers_set
        ).delete()
        FollowerChange.objects.filter(
            user=user,
            change_type=FollowerChangeStatusEnum.UNFOLLOW,
            user_pk__in=new_followers_set
        )
        # Add new changes
        FollowerChange.objects.bulk_create(changes, ignore_conflicts=True)

        # Add new followers
        new_follower_objs = [
            Follower(
                user=user,
                user_pk=pk,
                username=data["username"],
                full_name=data.get("full_name", ""),
                profile_pic_url=data.get("profile_pic_url", ""),
            )
            for pk, data in new_followers_dict.items() if pk in new_followers_set
        ]
        Follower.objects.bulk_create(new_follower_objs, ignore_conflicts=True)

        # add new followings
        new_following_objs = [
            Following(
                user=user,
                user_pk=pk,
                username=data["username"],
                full_name=data.get("full_name", ""),
                profile_pic_url=data.get("profile_pic_url", ""),
            )
            for pk, data in new_followings_dict.items() if pk in new_followings_set
        ]
        Following.objects.bulk_create(new_following_objs, ignore_conflicts=True)

        # remove expire follower, following
        if unfollowers_set:
            Follower.objects.filter(user=user, user_pk__in=unfollowers_set).delete()
        if unfollowings_set:
            Following.objects.filter(user=user, user_pk__in=unfollowings_set).delete()
