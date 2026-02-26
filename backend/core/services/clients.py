from django.db import transaction
from core.models import Membership

@transaction.atomic
def deactivate_client_service(*, client, requested_by=None):
    # 1) Desactivar cliente (soft)
    client.is_active = False
    client.save(update_fields=["is_active"])

    # 2) Desactivar membresías activas o programadas
    Membership.objects.filter(
        client=client,
        operational_status__in=["ACTIVE", "SCHEDULED"]
    ).update(operational_status="INACTIVE")

    return client


@transaction.atomic
def reactivate_client_service(*, client, requested_by=None):
    client.is_active = True
    client.save(update_fields=["is_active"])
    return client