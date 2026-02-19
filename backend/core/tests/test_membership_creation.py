import pytest
from django.utils import timezone
from core.services.memberships import create_membership_service


@pytest.mark.django_db
def test_create_first_membership_active(client_factory, gym_factory, plan_factory, user_factory):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, duration_days=30)
    user = user_factory(gym=gym)

    membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
    )

    assert membership.operational_status == "ACTIVE"
    assert membership.action == "INSCRIPTION"


@pytest.mark.django_db
def test_block_forced_active_when_active_exists(client_factory, gym_factory, plan_factory, user_factory):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, duration_days=30)
    user = user_factory(gym=gym)

    create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
    )

    with pytest.raises(Exception):
        create_membership_service(
            client=client,
            gym=gym,
            plan_id=plan.id,
            created_by=user,
            force_operational_status="ACTIVE",
        )


@pytest.mark.django_db
def test_renewal_is_scheduled_after_active(client_factory, gym_factory, plan_factory, user_factory):
    gym = gym_factory()
    client = client_factory(gym=gym)
    plan = plan_factory(gym=gym, duration_days=30)
    user = user_factory(gym=gym)

    first = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
    )

    second = create_membership_service(
        client=client,
        gym=gym,
        plan_id=plan.id,
        created_by=user,
    )

    assert second.operational_status == "SCHEDULED"
    assert second.start_date == first.end_date + timezone.timedelta(days=1)
