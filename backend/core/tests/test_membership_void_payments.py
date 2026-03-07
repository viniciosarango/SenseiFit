import pytest
from decimal import Decimal
from core.services.memberships import create_membership_service
from core.services.payments import register_payment, void_payment


@pytest.mark.django_db
def test_void_payment_recalculates_membership_finance(
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

    payment, membership = register_payment(
        membership_id=membership.id,
        amount=Decimal("5.00"),
        payment_method_id=payment_method.id,
        notes="Segundo abono",
        created_by=user,
    )

    membership.refresh_from_db()
    assert membership.paid_amount == Decimal("15.00")
    assert membership.balance == Decimal("14.00")
    assert membership.financial_status == "PARTIAL"

    void_payment(
        payment_id=payment.id,
        reason="Prueba de anulación",
        user=user,
    )

    membership.refresh_from_db()
    payment.refresh_from_db()

    assert payment.status == "VOID"
    assert membership.paid_amount == Decimal("10.00")
    assert membership.balance == Decimal("19.00")
    assert membership.financial_status == "PARTIAL"
    assert membership.payment_due_date is not None


@pytest.mark.django_db
def test_void_full_payment_restores_credit_due_date_with_enrollment_fee(
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
        enrollment_fee=Decimal("5.00"),
        paid_amount=Decimal("10.00"),
        payment_method_id=payment_method.id,
        credit_days=7,
    )

    payment, membership = register_payment(
        membership_id=membership.id,
        amount=Decimal("24.00"),
        payment_method_id=payment_method.id,
        notes="Pago total restante",
        created_by=user,
    )

    membership.refresh_from_db()
    assert membership.financial_status == "PAID"
    assert membership.balance == Decimal("0.00")
    assert membership.payment_due_date is None

    void_payment(
        payment_id=payment.id,
        reason="Anulación de pago total",
        user=user,
    )

    membership.refresh_from_db()
    payment.refresh_from_db()

    assert payment.status == "VOID"
    assert membership.paid_amount == Decimal("10.00")
    assert membership.balance == Decimal("24.00")
    assert membership.financial_status == "PARTIAL"
    assert membership.payment_due_date is not None