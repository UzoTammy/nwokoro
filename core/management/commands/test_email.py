from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail


class Command(BaseCommand):
    help = "Send a test email using current Django email settings."

    def add_arguments(self, parser):
        parser.add_argument("--to", required=True, help="Recipient email address")

    def handle(self, *args, **options):
        recipient = options["to"]

        if not settings.DEFAULT_FROM_EMAIL:
            raise CommandError("DEFAULT_FROM_EMAIL is not configured.")

        sent = send_mail(
            subject="SCusH Email Test",
            message="This is a test email from the nwokoro Django app.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )

        if sent == 1:
            self.stdout.write(self.style.SUCCESS(f"Email sent to {recipient}"))
            return

        raise CommandError("Email was not sent.")
