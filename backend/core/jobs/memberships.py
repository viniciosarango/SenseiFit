# core/jobs/memberships.py

from django.utils import timezone
from core.models import Membership
from core.utils.hikvision import sync_hikvision_async


def run_membership_lifecycle():

    today = timezone.localdate()

   # 1) VENCER ACTIVAS
    expired_qs = Membership.objects.filter(
        operational_status="ACTIVE",
        end_date__lt=today,
    )

    expired_count = expired_qs.update(
        operational_status="EXPIRED"
    )

   
    # 2) ACTIVAR MEMBRESÍAS PROGRAMADAS
    to_activate = Membership.objects.filter(
        operational_status="SCHEDULED",
        start_date__lte=today,
    ).exclude(
        operational_status="CANCELLED"
    ).order_by("start_date")


    activated_count = 0

    for membership in to_activate:
        # 🔒 Seguridad: no activar si ya hay una ACTIVE
        has_active = Membership.objects.filter(
            client=membership.client,
            gym=membership.gym,
            operational_status="ACTIVE"
        ).exists()

        if has_active:
            continue

        membership.operational_status = "ACTIVE"
        membership.save(update_fields=["operational_status"])

        sync_hikvision_async(membership)
        activated_count += 1

    return {
        "expired": expired_count,
        "activated": activated_count,
    }
