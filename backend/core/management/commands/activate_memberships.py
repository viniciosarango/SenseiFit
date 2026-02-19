from django.core.management.base import BaseCommand
from core.jobs.memberships import run_membership_lifecycle


class Command(BaseCommand):
    help = "Ejecuta el ciclo de vida de membresías (activar y vencer)"

    def handle(self, *args, **options):
        result = run_membership_lifecycle()

        self.stdout.write(
            self.style.SUCCESS(
                f"Membresías vencidas: {result['expired']} | "
                f"Membresías activadas: {result['activated']}"
            )
        )
