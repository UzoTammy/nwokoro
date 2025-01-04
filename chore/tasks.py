from django.utils import timezone
from celery import shared_task
from .models import Work, AssignWork, FinishedWork
from account.models import User


@shared_task
def delist_expired_job():
    assigned_works = AssignWork.objects.filter(state='active')
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
                reason='expired'
            )
            
@shared_task
def task_dishwash(work_id, worker_id, duration):
    
    work = Work.objects.get(pk=work_id)

    # Delist latest assigned work whose time is exhausted
    listed_works = AssignWork.objects.filter(work=work).filter(state='active')
    if listed_works.exists():
        latest = listed_works.latest('schedule')
        # 
        if latest.end_time <= timezone.now():
            latest.state = 'cancel'
            latest.save()

    worker = User.objects.get(pk=worker_id)
    assign_work = AssignWork(work=work, assigned=worker)
    assign_work.schedule = timezone.now()
    assign_work.end_time = assign_work.schedule + timezone.timedelta(hours=duration)
    assign_work.source = 'scheduled'
    assign_work.save()
    # send email
