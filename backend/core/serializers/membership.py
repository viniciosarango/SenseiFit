from django.utils import timezone
from rest_framework import serializers
from core.models import Membership, ClientGym



class MembershipSerializer(serializers.ModelSerializer):
    # Lectura amigable
    client_name = serializers.CharField(source="client", read_only=True)
    client_id_number = serializers.ReadOnlyField(source="client.id_number")
    plan_name = serializers.ReadOnlyField(source="plan.name")
    plan_type = serializers.ReadOnlyField(source="plan.plan_type")
    gym_name = serializers.ReadOnlyField(source="gym.name")
    freeze_days_current = serializers.SerializerMethodField()

    # Campos de control para el servicio
    paid_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        write_only=True,
        required=False,
        default=0
    )

    payment_method_id = serializers.IntegerField(write_only=True, required=False)
    is_upgrade = serializers.BooleanField(write_only=True, default=False)
    plan_id = serializers.IntegerField(write_only=True)

    requested_start_date = serializers.DateField(
        write_only=True,
        required=False,
        allow_null=True
    )

    operational_status = serializers.ChoiceField(
        choices=["ACTIVE", "SCHEDULED", "EXPIRED", "CANCELLED", "INACTIVE", "FROZEN"],
        required=False
    )

    class Meta:
        model = Membership
        fields = [
            "id", "created_at",
            "client", "plan", "plan_id", "plan_name", "plan_type", "gym",
            "client_name", "client_id_number", "gym_name",
            "start_date", "requested_start_date", "end_date", "payment_due_date",
            "original_price", "discount_percent_applied",
            "final_price", "total_amount", "paid_amount", "balance",
            "financial_status", "operational_status", "notes",
            "payment_method_id", "is_upgrade",
            "sessions_total", "sessions_consumed", "sessions_remaining",
            "courtesy_qty","freeze_start_date", "total_freeze_days",
            "freeze_days_current"
        ]

        read_only_fields = [
            "id", "gym", "start_date", "end_date", "payment_due_date",
            "original_price", "final_price", "total_amount", "balance",
            "financial_status", "plan", "sessions_remaining"
        ]


    def get_freeze_days_current(self, obj):
        if obj.operational_status == "FROZEN" and obj.freeze_start_date:
            today = timezone.localdate()
            return (today - obj.freeze_start_date).days + obj.total_freeze_days
        return obj.total_freeze_days

    def validate(self, data):
        """
        ⚠️ Nota importante:
        En tu nuevo diseño el gym correcto se determina en la VIEW (por rol).
        Aquí solo validamos reglas de negocio base, y evitamos client.gym.
        """
        request = self.context.get("request")
        if not request:
            return data

        user = request.user

        # Solo ADMIN puede forzar operational_status
        if "operational_status" in data:
            if not user.is_superuser and user.role != user.Roles.ADMIN:
                raise serializers.ValidationError(
                    {"operational_status": "No tienes permisos para forzar el estado de la membresía."}
                )

        return data