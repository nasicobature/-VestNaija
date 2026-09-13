from django.core.management.base import BaseCommand

from accounts.services import send_due_kyc_approval_emails


class Command(BaseCommand):
    help = "Send queued 'you're verified' emails whose 24-hour delay has elapsed. Run this periodically (e.g. every 15 minutes) from a scheduled task or cron job."

    def handle(self, *args, **options):
        sent = send_due_kyc_approval_emails()
        self.stdout.write(self.style.SUCCESS(f"Sent {sent} queued KYC approval email(s)."))
