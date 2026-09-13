from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from audit.services import log_audit
from payments.models import Withdrawal

# Known demo-login usernames from earlier seed_demo runs. Their passwords are
# readable in this repo's git history, so any account under these usernames
# must never stay active outside local development.
KNOWN_DEMO_USERNAMES = ["nasir@example.com"]


class Command(BaseCommand):
    help = "Deactivate any known demo-login accounts and cancel their pending withdrawals. Safe to run on every deploy."

    def handle(self, *args, **options):
        locked = 0
        cancelled = 0
        for username in KNOWN_DEMO_USERNAMES:
            user = User.objects.filter(username=username).first()
            if not user:
                continue
            if user.is_active:
                user.is_active = False
                user.save(update_fields=["is_active"])
                log_audit(None, "demo_account_locked_down", user, {"username": username})
                locked += 1
            pending = Withdrawal.objects.filter(user=user, status=Withdrawal.Status.PENDING)
            for withdrawal in pending:
                withdrawal.status = Withdrawal.Status.CANCELLED
                withdrawal.save(update_fields=["status"])
                log_audit(None, "demo_account_withdrawal_cancelled", withdrawal, {"amount": str(withdrawal.amount)})
                cancelled += 1
        self.stdout.write(self.style.SUCCESS(f"Locked {locked} demo account(s); cancelled {cancelled} pending withdrawal(s)."))
