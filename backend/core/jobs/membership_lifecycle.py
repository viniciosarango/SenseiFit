from django.utils import timezone
from core.models import Membership
from core.utils.hikvision import sync_hikvision_async


def run_membership_lifecycle():
    """
    Job diario:
    1) Vence membresías ACTIVAS cuyo end_date ya pasó
    2) Activa membresías PROGRAMADAS cuyo start_date llegó
    """

    today = timezone.localdate()

    # 1) Vencer activas
    expired = Membership.objects.filter(
        operational_status="ACTIVE",
        end_date__lt=today,
    )
    expired_count = expired.update(operational_status="EXPIRED")

    # 2) Activar programadas
    to_activate = Membership.objects.filter(
        operational_status="SCHEDULED",
        start_date__lte=today,
    )

    activated_count = 0
    for membership in to_activate:
        membership.operational_status = "ACTIVE"
        membership.save(update_fields=["operational_status"])
        sync_hikvision_async(membership)
        activated_count += 1

    return {
        "expired": expired_count,
        "activated": activated_count,
    }
