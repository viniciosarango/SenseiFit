import pytest
from decimal import Decimal
from django.utils import timezone

from core.services.memberships import (
    create_membership_service,
    upgrade_membership_service,
    MembershipError,
)


@pytest.mark.django_db
def test_upgrade_time_membership_applies_credit_and_cancels_previous(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    base_plan = plan_factory(
        gym=gym,
        plan_type="TIME",
        price=Decimal("30.00"),
        duration_days=30,
        name="Plan Mensual",
    )
    upgrade_plan = plan_factory(
        gym=gym,
        plan_type="TIME",
        price=Decimal("75.00"),
        duration_days=90,
        name="Plan Trimestral",
    )

    membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=base_plan.id,
        created_by=user,
        sale_type="CASH",
        paid_amount=Decimal("30.00"),
        payment_method_id=payment_method.id,
    )

    membership.end_date = timezone.localdate() + timezone.timedelta(days=20)
    membership.save(update_fields=["end_date", "renovation_date"])

    upgraded = upgrade_membership_service(
        client=client,
        gym=gym,
        new_plan_id=upgrade_plan.id,
        payment_method_id=payment_method.id,
        created_by=user,
        paid_amount=Decimal("0.00"),
        sale_type="CREDIT",
        notes="Upgrade TIME test",
    )

    membership.refresh_from_db()
    upgraded.refresh_from_db()

    assert membership.operational_status == "CANCELLED"
    assert membership.end_date == timezone.localdate()
    assert upgraded.operational_status == "ACTIVE"
    assert upgraded.plan_id == upgrade_plan.id
    assert upgraded.action == "UPGRADE"
    assert upgraded.upgrade_credit == Decimal("20.00")
    assert upgraded.total_amount == Decimal("55.00")
    assert upgraded.balance == Decimal("55.00")
    assert upgraded.financial_status == "PENDING"


@pytest.mark.django_db
def test_upgrade_sessions_membership_applies_credit_by_remaining_sessions(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    base_plan = plan_factory(
        gym=gym,
        plan_type="SESSIONS",
        price=Decimal("25.00"),
        total_sessions=10,
        duration_days=30,
        name="Plan 10 sesiones",
    )
    upgrade_plan = plan_factory(
        gym=gym,
        plan_type="SESSIONS",
        price=Decimal("40.00"),
        total_sessions=20,
        duration_days=90,
        name="Plan 20 sesiones",
    )

    membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=base_plan.id,
        created_by=user,
        sale_type="CASH",
        paid_amount=Decimal("25.00"),
        payment_method_id=payment_method.id,
    )

    membership.sessions_consumed = 4
    membership.save(update_fields=["sessions_consumed"])

    upgraded = upgrade_membership_service(
        client=client,
        gym=gym,
        new_plan_id=upgrade_plan.id,
        payment_method_id=payment_method.id,
        created_by=user,
        paid_amount=Decimal("0.00"),
        sale_type="CREDIT",
        notes="Upgrade SESSIONS test",
    )

    membership.refresh_from_db()
    upgraded.refresh_from_db()

    assert membership.operational_status == "CANCELLED"
    assert upgraded.operational_status == "ACTIVE"
    assert upgraded.plan_id == upgrade_plan.id
    assert upgraded.action == "UPGRADE"
    assert upgraded.upgrade_credit == Decimal("15.00")
    assert upgraded.total_amount == Decimal("25.00")
    assert upgraded.balance == Decimal("25.00")
    assert upgraded.financial_status == "PENDING"


@pytest.mark.django_db
def test_upgrade_rejects_membership_with_pending_balance(
    client_factory, gym_factory, plan_factory, user_factory, payment_method_factory
):
    gym = gym_factory()
    client = client_factory(gym=gym)
    user = user_factory(gym=gym)
    payment_method = payment_method_factory(gym=gym)

    base_plan = plan_factory(
        gym=gym,
        plan_type="TIME",
        price=Decimal("29.00"),
        duration_days=30,
        name="Plan Mensual",
    )
    upgrade_plan = plan_factory(
        gym=gym,
        plan_type="TIME",
        price=Decimal("75.00"),
        duration_days=90,
        name="Plan Trimestral",
    )

    create_membership_service(
        client=client,
        gym=gym,
        plan_id=base_plan.id,
        created_by=user,
        sale_type="CREDIT",
        paid_amount=Decimal("10.00"),
        payment_method_id=payment_method.id,
        credit_days=7,
    )

    with pytest.raises(MembershipError):
        upgrade_membership_service(
            client=client,
            gym=gym,
            new_plan_id=upgrade_plan.id,
            payment_method_id=payment_method.id,
            created_by=user,
            paid_amount=Decimal("0.00"),
            sale_type="CREDIT",
            notes="Upgrade con deuda",
        )