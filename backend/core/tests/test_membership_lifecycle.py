import pytest
from django.utils import timezone
from core.jobs.memberships import run_membership_lifecycle


@pytest.mark.django_db
def test_lifecycle_activates_and_expires(membership_factory):
    today = timezone.localdate()

    active = membership_factory(
        operational_status="ACTIVE",
        start_date=today - timezone.timedelta(days=30),
        end_date=today - timezone.timedelta(days=1),
    )    

    scheduled = membership_factory(
        operational_status="SCHEDULED",
        start_date=today,
        end_date=today + timezone.timedelta(days=29),
    )

    result = run_membership_lifecycle()

    active.refresh_from_db()
    scheduled.refresh_from_db()

    assert result["expired"] == 1
    assert result["activated"] == 1
    assert active.operational_status == "EXPIRED"
    assert scheduled.operational_status == "ACTIVE"