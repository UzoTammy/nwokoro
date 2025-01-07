from django.utils import timezone
from celery import shared_task
from .models import AssignWork, FinishedWork
from .emails import Email


@shared_task
def delist_expired_job():
    "Remove expired jobs from job list after 3 hours"
    assigned_works = AssignWork.objects.filter(state__in=['active', 'repeat'])
    for assigned_work in assigned_works:
        if assigned_work.is_expired():
            assigned_work.state='cancel'
            assigned_work.save()

            FinishedWork.objects.create(
                work=assigned_work.work,
                worker=assigned_work.assigned,
                base_point=0,
                bonus_point=0,
                scheduled_time=assigned_work.schedule,
                end_time=assigned_work.end_time,
                finished_time=timezone.now(),
                state='cancel',
                reason='expired',
                rating=0
            )

@shared_task
def send_me_mail():
    Email.email_dashboard()

@shared_task
def schedule_job():
    """1. go to the job register"""
 

