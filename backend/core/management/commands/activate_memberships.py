from django.core.management.base import BaseCommand
from core.jobs.memberships import run_membership_lifecycle


class Command(BaseCommand):
    help = "Sincroniza el ciclo de vida de membresías"

    def handle(self, *args, **options):
        result = run_membership_lifecycle()

        self.stdout.write(
            self.style.SUCCESS(
                f"[Membership Sync] expired={result['expired']} activated={result['activated']}"
            )
        )