import pytest
from decimal import Decimal

from core.services.memberships import create_membership_service


@pytest.mark.django_db
def test_time_plan_renewal_queue_does_not_block_sessions_plan(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    time_plan = plan_factory(gym=gym, plan_type="TIME", price=Decimal("29.00"), duration_days=30)
    sessions_plan = plan_factory(gym=gym, plan_type="SESSIONS", price=Decimal("40.00"), total_sessions=20)

    time_membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=time_plan.id,
        created_by=user,
        sale_type="CASH",
        paid_amount=Decimal("29.00"),
        payment_method_id=payment_method.id,
    )

    sessions_membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=sessions_plan.id,
        created_by=user,
        sale_type="CASH",
        paid_amount=Decimal("40.00"),
        payment_method_id=payment_method.id,
    )

    assert time_membership.operational_status == "ACTIVE"
    assert sessions_membership.operational_status == "ACTIVE"
    assert time_membership.plan.plan_type == "TIME"
    assert sessions_membership.plan.plan_type == "SESSIONS"