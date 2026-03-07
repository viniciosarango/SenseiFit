import pytest
from decimal import Decimal
from core.services.memberships import create_membership_service
from core.services.payments import register_payment, PaymentError


@pytest.mark.django_db
def test_credit_membership_allows_follow_up_payment(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("29.00"))
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
        sale_type="CREDIT",
        paid_amount=Decimal("10.00"),
        payment_method_id=payment_method.id,
        credit_days=7,
    )

    payment, updated_membership = register_payment(
        membership_id=membership.id,
        amount=Decimal("19.00"),
        payment_method_id=payment_method.id,
        notes="Pago restante",
        created_by=user,
    )

    assert payment.amount == Decimal("19.00")
    assert updated_membership.financial_status == "PAID"
    assert updated_membership.balance == Decimal("0.00")
    assert updated_membership.payment_due_date is None


@pytest.mark.django_db
def test_cash_membership_rejects_follow_up_payment(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("29.00"))
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

    with pytest.raises(PaymentError):
        register_payment(
            membership_id=membership.id,
            amount=Decimal("1.00"),
            payment_method_id=payment_method.id,
            notes="Pago extra",
            created_by=user,
        )