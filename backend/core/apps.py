from django.apps import AppConfig
import os


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Cargar signals
        #import backend.core.signals

        # Evitar doble scheduler en runserver
        if os.environ.get("RUN_MAIN") != "true":
            return

        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore
        from core.jobs.memberships import run_membership_lifecycle

        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            run_membership_lifecycle,
            trigger="interval",
            hours=24,
            id="run_membership_lifecycle",
            replace_existing=True,
        )

        scheduler.start()
