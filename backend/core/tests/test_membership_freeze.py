import pytest
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

from core.services.memberships import (
    create_membership_service,
    freeze_membership_service,
    unfreeze_membership_service,
    MembershipError,
)


@pytest.mark.django_db
def test_freeze_and_unfreeze_extend_end_date(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory, settings
):
    settings.CANCEL_PIN = "1234"

    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("29.00"), duration_days=30)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
        sale_type="CASH",
        paid_amount=Decimal("29.00"),
        payment_method_id=payment_method.id,
    )

    original_end_date = membership.end_date

    freeze_membership_service(
        membership=membership,
        requested_by=user,
        pin="1234",
    )

    membership.refresh_from_db()
    assert membership.operational_status == "FROZEN"
    assert membership.freeze_start_date == timezone.localdate()

    membership.freeze_start_date = timezone.localdate() - timezone.timedelta(days=3)
    membership.save(update_fields=["freeze_start_date"])

    unfreeze_membership_service(
        membership=membership,
        requested_by=user,
        pin="1234",
    )

    membership.refresh_from_db()
    assert membership.operational_status == "ACTIVE"
    assert membership.end_date == original_end_date + timezone.timedelta(days=3)
    assert membership.renovation_date == membership.end_date + timezone.timedelta(days=1)
    assert membership.total_freeze_days == 3


@pytest.mark.django_db
def test_freeze_rejects_membership_with_scheduled_queue(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory, settings
):
    settings.CANCEL_PIN = "1234"

    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("29.00"), duration_days=30)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
        sale_type="CASH",
        paid_amount=Decimal("29.00"),
        payment_method_id=payment_method.id,
    )

    second = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
        sale_type="CASH",
        paid_amount=Decimal("29.00"),
        payment_method_id=payment_method.id,
    )

    active = second.client.memberships.filter(operational_status="ACTIVE").first()

    with pytest.raises(MembershipError):
        freeze_membership_service(
            membership=active,
            requested_by=user,
            pin="1234",
        )