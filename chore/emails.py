from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.urls import reverse
from account.models import User

class Email:

    def email_admin():
        subject = "Routine email to admin on chores"
        from_email = "no-reply@chores.com"
        to_email = ["nwokorouzo77@gmail.com"]

        # Load the HTML content
        html_content = render_to_string('chore/mails/admin.html', {
            'workers': User.objects.filter(is_staff=False).count(),
            'moderators': User.objects.filter(is_staff=True).count()
            })
        # Create the email message
        msg = EmailMultiAlternatives(subject, "plain text", from_email, to_email)
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