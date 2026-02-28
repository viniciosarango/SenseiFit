from rest_framework import serializers
from core.models import Client, Membership
from core.serializers.membership import MembershipSerializer

from core.models import Payment
from core.serializers.payment import PaymentSerializer
from django.db.models import Sum
from decimal import Decimal




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
    
    payments = serializers.SerializerMethodField()

    def get_payments(self, obj: Client):
        qs = (
            Payment.objects
            .filter(membership__client=obj)
            .select_related("membership", "membership__plan", "membership__gym", "payment_method")
            .order_by("-payment_date", "-id")
        )
        return PaymentSerializer(qs, many=True, context=self.context).data
    
    summary = serializers.SerializerMethodField()

    def get_summary(self, obj: Client):
        memberships = obj.memberships.filter(operational_status__in=["ACTIVE", "SCHEDULED"])

        total_amount = memberships.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        total_paid = memberships.aggregate(paid=Sum("payments__amount"))["paid"] or Decimal("0.00")
        balance = total_amount - total_paid
        if balance < 0:
            balance = Decimal("0.00")

        last_payment = (
            obj.memberships
            .values("payments__payment_date", "payments__amount", "payments__status", "payments__payment_method__name")
            .order_by("-payments__payment_date")
            #.values("payments__created_at", "payments__amount", "payments__status", "payments__method__name")
            .exclude(payments__id__isnull=True)
            #.order_by("-payments__created_at")
            .first()
        )

        return {
            "total_amount": float(total_amount),
            "total_paid": float(total_paid),
            "outstanding_balance": float(balance),
            "last_payment": last_payment,
        }