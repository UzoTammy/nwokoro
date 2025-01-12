from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.urls import reverse
from account.models import Transaction
from .models import FinishedWork
from django.db.models.aggregates import Sum
from account.models import User
from django.db.models.functions import TruncWeek

class Email:

    def get_context(workers, finished_works, transactions):
        # workers = User.objects.filter(is_staff=False)
        # finished_works = FinishedWork.objects.all()
        # transactions = Transaction.objects.all()
        
        workers_pk = workers.values_list('pk', flat=True)

        weekly_performance = [(
            finished_works.filter(worker__pk=pk).annotate(week=TruncWeek('finished_time'))  # Replace 'date_field' with your model's date/datetime field
                .values('week')
                .annotate(
                    base_point=Sum('base_point'),
                    bonus_point=Sum('bonus_point')
                )  # Replace 'some_numeric_field' with the field to sum up
                .order_by('week').last()  # Optional: order by week
            ) for pk in workers_pk]
            # Attach a user to each weekly performance
    
        if any(weekly_performance):
            wp = []
            for p in zip(workers_pk, weekly_performance):
                p[1]['worker'] = User.objects.get(pk=p[0]).username
                wp.append(p[1])
            weekly_performance = wp  

        return {
            'jobs_executed': finished_works.filter(state='done').count(),
            'jobs_cancelled': finished_works.filter(state='cancel').count(),
            'points': transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0,
            'points_redeemed': transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0,
            'base_points': finished_works.aggregate(Sum('base_point'))['base_point__sum'] or 0,
            'bonus_points': finished_works.aggregate(Sum('bonus_point'))['bonus_point__sum'] or 0,
            'workers': [
                {
                    'pk': worker.pk,
                    'username': worker.username,
                    'points': worker.points,
                    'jobs': worker.transactions.filter(amount__gt=0).count(),
                    'redeem': worker.transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0,
                } for worker in workers
            ],
            'weekly_performance': weekly_performance
        }
    
     
    def email_dashboard():
        from_email = "no-reply@chores.com"

        # Load the HTML content
        workers = User.objects.filter(is_staff=False)
        finished_works = FinishedWork.objects.all()
        transactions = Transaction.objects.all()

        subject = "Weekly chores report"
        to_email = [ worker.email for worker in User.objects.all() ]

        html_content = render_to_string('chore/mails/dashboard.html', Email.get_context(workers, finished_works, transactions))
        
        # Create the email message
        msg = EmailMultiAlternatives(subject, "plain text", from_email, to_email,
                                     headers={"Reply-To": "nwokorouzo@gmail.com"},)
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send()
            # return HttpResponse("Email sent successfully!")
        except Exception as e:
            return HttpResponse(f"Failed to send email: {e}")

    def delegate_send_email(request, form):
        """Send email when work is delegated"""
        subject = f"Delegated Job for {form.instance.schedule}"
        from_email = "no-reply@chores.com"
        to_email = [request.user.email, form.instance.assigned.email]

        
        # Generate the URL dynamically
        relative_url = reverse('assign-work-list')  # Replace 'home' with the name of your URL pattern
        site_url = request.build_absolute_uri(relative_url)

        # Load the HTML content
        html_content = render_to_string('chore/mails/delegate.html', {
            'name': f'{form.instance.assigned.username}',
            'site_url': site_url
            })
        # Create the email message
        msg = EmailMultiAlternatives(subject, "plain text", from_email, to_email)
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send()
            # return HttpResponse("Email sent successfully!")
        except Exception as e:
            return HttpResponse(f"Failed to send email: {e}")

    def initiate_send_email(request, form):
        """Send email when work is initiated"""
        subject = f"Initiated Job by {form.instance.worker.username} - {form.instance.pk}"
        from_email = "no-reply@chores.com"
        to_email = [request.user.email, form.instance.worker.email]

        # Load the HTML content
        html_content = render_to_string('chore/mails/initiate.html', {
            'name': f'{form.instance.worker.username}',
            # 'site_url': site_url
            })
        # Create the email message
        msg = EmailMultiAlternatives(subject, "plain text", from_email, to_email)
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send()
            
        except Exception as e:
            return HttpResponse(f"Failed to send email: {e}")

    def approve_send_email(request, form):
        """Send email when work is approved"""
        subject = f"Initiated Job by {form.instance.worker.username} - {form.instance.pk}"
        from_email = "no-reply@chores.com"
        to_email = [request.user.email, form.instance.worker.email]

        # Generate the URL dynamically
        relative_url = reverse('assign-work-list')  # Replace 'home' with the name of your URL pattern
        site_url = request.build_absolute_uri(relative_url)

        # Load the HTML content
        html_content = render_to_string('chore/mails/initiate_approve.html', {
            'name': f'{form.instance.worker.username}',
            'site_url': site_url
            })
        
        # Create the email message
        msg = EmailMultiAlternatives(subject, "plain text", from_email, to_email)
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send()

        except Exception as e:
            return HttpResponse(f"Failed to send email: {e}")

        # continue