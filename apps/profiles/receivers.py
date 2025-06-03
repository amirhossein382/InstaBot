import json

from django.dispatch import receiver
from django.contrib.auth import user_logged_out
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from .signals import profile_initialized

task_name = "analyze_follow_data_user_{user_id}"


@receiver(profile_initialized)
def start_periodic_analysis(sender, user, **kwargs):
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=2,
        period=IntervalSchedule.MINUTES,
    )
    task_name_ = task_name.format(user_id=user.id)
    if not PeriodicTask.objects.filter(name=task_name).exists():
        PeriodicTask.objects.create(
            interval=schedule,
            name=task_name_,
            task="apps.profiles.tasks.analyze_and_update_follow_data",
            args=json.dumps([user.id, ]),
            one_off=False,
            enabled=True,
        )


@receiver(user_logged_out)
def end_periodic_analysis(sender, request, user, **kwargs):
    try:
        task = PeriodicTask.objects.get(name=task_name.format(user_id=user.id))
    except PeriodicTask.DoesNotExist:
        pass
    else:
        task.delete()
