from django.utils import timezone
from core.models import Membership
from core.utils.hikvision import sync_hikvision_async


def run_membership_lifecycle():
    today = timezone.localdate()

    expired_count = 0
    activated_count = 0

    active_to_expire = (
        Membership.objects.filter(
            operational_status="ACTIVE",
            end_date__lt=today,
        )
        .select_related("plan", "client", "gym")
        .order_by("end_date", "id")
    )

    for membership in active_to_expire:
        membership.operational_status = "EXPIRED"
        membership.save(update_fields=["operational_status"])
        sync_hikvision_async(membership)
        expired_count += 1

    to_activate = (
        Membership.objects.filter(
            operational_status="SCHEDULED",
            start_date__lte=today,
        )
        .select_related("plan", "client", "gym")
        .order_by("start_date", "id")
    )

    for membership in to_activate:
        has_active_same_type = Membership.objects.filter(
            client=membership.client,
            gym=membership.gym,
            plan__plan_type=membership.plan.plan_type,
            operational_status="ACTIVE",
        ).exclude(id=membership.id).exists()

        if has_active_same_type:
            continue

        membership.operational_status = "ACTIVE"
        membership.save(update_fields=["operational_status"])
        sync_hikvision_async(membership)
        activated_count += 1

    return {
        "expired": expired_count,
        "activated": activated_count,
    }