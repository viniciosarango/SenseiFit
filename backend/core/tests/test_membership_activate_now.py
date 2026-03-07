import pytest
from decimal import Decimal
from django.utils import timezone

from core.services.memberships import (
    create_membership_service,
    activate_membership_now,
)


@pytest.mark.django_db
def test_activate_now_moves_scheduled_membership_and_reorders_queue(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("29.00"), duration_days=30)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    first = create_membership_service(
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

    third = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
        sale_type="CASH",
        paid_amount=Decimal("29.00"),
        payment_method_id=payment_method.id,
    )

    first.operational_status = "EXPIRED"
    first.save(update_fields=["operational_status"])

    original_third_start = third.start_date

    activate_membership_now(
        membership=second,
        activated_by=user,
    )

    second.refresh_from_db()
    third.refresh_from_db()

    assert second.operational_status == "ACTIVE"
    assert second.start_date == timezone.localdate()
    assert second.end_date == timezone.localdate() + timezone.timedelta(days=29)
    assert second.renovation_date == second.end_date + timezone.timedelta(days=1)

    assert third.start_date != original_third_start    
    assert third.start_date == second.end_date + timezone.timedelta(days=1)
    assert third.renovation_date == third.end_date + timezone.timedelta(days=1)