import pytest
from decimal import Decimal

from core.services.memberships import create_membership_service


@pytest.mark.django_db
def test_membership_pricing_with_discount_and_enrollment_fee_cash(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("30.00"), duration_days=30)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
        sale_type="CASH",
        discount_percent=10,
        enrollment_fee=Decimal("5.00"),
        paid_amount=Decimal("32.00"),
        payment_method_id=payment_method.id,
        notes="Prueba pricing cash",
    )

    assert membership.original_price == Decimal("30.00")
    assert membership.discount_percent_applied == Decimal("10.00")
    assert membership.final_price == Decimal("27.00")
    assert membership.enrollment_fee_applied == Decimal("5.00")
    assert membership.total_amount == Decimal("32.00")
    assert membership.paid_amount == Decimal("32.00")
    assert membership.balance == Decimal("0.00")
    assert membership.financial_status == "PAID"


@pytest.mark.django_db
def test_membership_pricing_with_discount_and_enrollment_fee_credit(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("50.00"), duration_days=30)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
        sale_type="CREDIT",
        discount_percent=20,
        enrollment_fee=Decimal("10.00"),
        paid_amount=Decimal("20.00"),
        payment_method_id=payment_method.id,
        credit_days=7,
        notes="Prueba pricing credit",
    )

    assert membership.original_price == Decimal("50.00")
    assert membership.discount_percent_applied == Decimal("20.00")
    assert membership.final_price == Decimal("40.00")
    assert membership.enrollment_fee_applied == Decimal("10.00")
    assert membership.total_amount == Decimal("50.00")
    assert membership.paid_amount == Decimal("20.00")
    assert membership.balance == Decimal("30.00")
    assert membership.financial_status == "PARTIAL"
    assert membership.payment_due_date is not None