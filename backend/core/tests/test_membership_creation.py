import pytest
from decimal import Decimal
from django.utils import timezone
from core.services.memberships import create_membership_service, MembershipError


@pytest.mark.django_db
def test_create_cash_membership_requires_full_payment(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, duration_days=30, price=Decimal("29.00"))
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

    assert membership.sale_type == "CASH"
    assert membership.financial_status == "PAID"
    assert membership.balance == Decimal("0.00")
    assert membership.payment_due_date is None
    assert membership.operational_status == "ACTIVE"
    assert membership.action == "INSCRIPTION"


@pytest.mark.django_db
def test_cash_membership_rejects_partial_payment(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, duration_days=30, price=Decimal("29.00"))
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    with pytest.raises(MembershipError):
        create_membership_service(
            client=client,
            gym=gym,
            plan_id=plan.id,
            created_by=user,
            sale_type="CASH",
            paid_amount=Decimal("10.00"),
            payment_method_id=payment_method.id,
        )


@pytest.mark.django_db
def test_credit_membership_allows_partial_payment_and_due_date(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, duration_days=30, price=Decimal("29.00"))
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

    assert membership.sale_type == "CREDIT"
    assert membership.financial_status == "PARTIAL"
    assert membership.balance == Decimal("19.00")
    assert membership.payment_due_date == timezone.localdate() + timezone.timedelta(days=7)


@pytest.mark.django_db
def test_renewal_is_scheduled_after_active(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, duration_days=30, price=Decimal("29.00"))
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

    assert second.operational_status == "SCHEDULED"
    assert second.start_date == first.end_date + timezone.timedelta(days=1)
    assert second.action == "RENEWAL"