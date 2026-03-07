import pytest
from decimal import Decimal

from core.services.memberships import (
    create_membership_service,
    cancel_membership_service,
    MembershipError,
)


@pytest.mark.django_db
def test_cancel_membership_sets_cancelled_and_clears_due_date(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory, settings
):
    settings.CANCEL_PIN = "1234"

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

    assert membership.payment_due_date is not None

    cancel_membership_service(
        membership=membership,
        requested_by=user,
        pin="1234",
        reason="Prueba de cancelacion",
    )

    membership.refresh_from_db()
    assert membership.operational_status == "CANCELLED"
    assert membership.payment_due_date is None
    assert "Prueba de cancelacion" in (membership.notes or "")


@pytest.mark.django_db
def test_cancel_membership_rejects_invalid_pin(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory, settings
):
    settings.CANCEL_PIN = "1234"

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

    with pytest.raises(MembershipError):
        cancel_membership_service(
            membership=membership,
            requested_by=user,
            pin="9999",
            reason="PIN invalido",
        )