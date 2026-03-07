import pytest
from decimal import Decimal
from django.utils import timezone

from core.services.memberships import create_membership_service, MembershipError


@pytest.mark.django_db
def test_credit_rejects_due_date_in_past(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("29.00"))
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    with pytest.raises(MembershipError):
        create_membership_service(
            client=client,
            gym=gym,
            plan_id=plan.id,
            created_by=user,
            sale_type="CREDIT",
            paid_amount=Decimal("10.00"),
            payment_method_id=payment_method.id,
            payment_due_date=timezone.localdate(),
        )


@pytest.mark.django_db
def test_credit_rejects_non_positive_credit_days(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("29.00"))
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    with pytest.raises(MembershipError):
        create_membership_service(
            client=client,
            gym=gym,
            plan_id=plan.id,
            created_by=user,
            sale_type="CREDIT",
            paid_amount=Decimal("10.00"),
            payment_method_id=payment_method.id,
            credit_days=0,
        )


@pytest.mark.django_db
def test_cash_rejects_missing_full_payment_even_with_discounted_total(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, price=Decimal("30.00"))
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    with pytest.raises(MembershipError):
        create_membership_service(
            client=client,
            gym=gym,
            plan_id=plan.id,
            created_by=user,
            sale_type="CASH",
            discount_percent=10,
            enrollment_fee=Decimal("5.00"),
            paid_amount=Decimal("31.99"),
            payment_method_id=payment_method.id,
        )