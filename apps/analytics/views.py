from django.db.models import Max, Subquery, OuterRef
from rest_framework import views, status
from rest_framework.response import Response

from apps.account.models import InstagramAccount
from apps.account.exceptions import base_response_with_error
from apps.profiles.models import Post
from .serializers import (
    DailyFollowerGrowthLogSerializer, TopPostSerializer, BestPostTimeStatesSerializer
)
from .models import DailyFollowerGrowthLog, TopPosts, BestTimeStats
from .services import AnalyticsService

_analytics_svc = AnalyticsService()


class DailyFollowerGrowthLogAPIView(views.APIView):
    serializer_class = DailyFollowerGrowthLogSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return DailyFollowerGrowthLog.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        try:
            logs = self.get_queryset()
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = DailyFollowerGrowthLogSerializer(logs, many=True)
        return Response(serializer.data)


class TopPostListAPIView(views.APIView):
    serializer_class = TopPostSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return TopPosts.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        try:
            top_posts = self.get_queryset()
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = TopPostSerializer(top_posts, many=True)
        return Response(serializer.data)


class TopPostDetailAPIView(views.APIView):
    serializer_class = TopPostSerializer

    def get_queryset(self, post_pk):
        account = InstagramAccount.objects.get(user=self.request.user)
        post = Post.objects.get(pk=post_pk)
        return TopPosts.objects.get(account=account, post=post)

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        try:
            top_post = self.get_queryset(post_pk=pk)
        except (InstagramAccount.DoesNotExist, Post.DoesNotExist, TopPosts.DoesNotExist) as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = TopPostSerializer(top_post)
        return Response(serializer.data)


class BestTimeToPostAPIView(views.APIView):
    serializer_class = BestPostTimeStatesSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        base = BestTimeStats.objects.filter(account=account)
        best_per_day = (
            base
            .values("weekday")
            .annotate(best_score=Max("avg_score"))
        )
        return base.filter(
            avg_score__in=Subquery(
                best_per_day.filter(
                    weekday=OuterRef("weekday")
                ).values("best_score")
            )
        )

    def get(self, request, **kwargs):
        try:
            query_set = self.get_queryset()
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(instance=query_set, many=True)
        return Response(serializer.data)


class FollowerSummaryAPIView(views.APIView):

    def get(self, request, *args, **kwargs):
        account = request.user.instagram_account
        days = int(request.query_params.get("days", 7))

        data = _analytics_svc.get_follower_summary(account, days)

        return Response({
            "range": f"last_{days}_days",
            "new_followers": data["new_followers"],
            "lost_followers": data["lost_followers"],
            "net_growth": data["new_followers"] - data["lost_followers"],
        })
