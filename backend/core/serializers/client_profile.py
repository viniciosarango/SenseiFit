from rest_framework import serializers
from core.models import Client, Membership
from core.serializers.membership import MembershipSerializer


class ClientProfileSerializer(serializers.Serializer):
    client = serializers.SerializerMethodField()
    memberships = serializers.SerializerMethodField()
    active_membership = serializers.SerializerMethodField()

    def get_client(self, obj: Client):
        # Reutiliza el ClientSerializer que ya usas en /clients/{id}/
        from core.serializers.client import ClientSerializer
        return ClientSerializer(obj, context=self.context).data

    def get_memberships(self, obj: Client):
        qs = (
            Membership.objects
            .filter(client=obj)
            .select_related("gym", "plan")
            .order_by("-created_at")
        )
        return MembershipSerializer(qs, many=True, context=self.context).data

    def get_active_membership(self, obj: Client):
        # Si quieres estrictamente la "ACTIVE"
        m = (
            Membership.objects
            .filter(client=obj, operational_status="ACTIVE")
            .select_related("gym", "plan")
            .order_by("-start_date", "-created_at")
            .first()
        )
        return MembershipSerializer(m, context=self.context).data if m else None