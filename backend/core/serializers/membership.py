from rest_framework import serializers
from core.models import Membership


class MembershipSerializer(serializers.ModelSerializer):

    # Lectura amigable
    client_name = serializers.CharField(source="client", read_only=True)
    client_id_number = serializers.ReadOnlyField(source="client.id_number")
    plan_name = serializers.ReadOnlyField(source="plan.name")
    plan_type = serializers.ReadOnlyField(source="plan.plan_type")
    gym_name = serializers.ReadOnlyField(source="gym.name")

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
            "courtesy_qty",
        ]

        read_only_fields = [
            "id", "gym", "start_date", "end_date", "payment_due_date",
            "original_price", "final_price", "total_amount", "balance",
            "financial_status", "plan", "sessions_remaining"
        ]

    def validate(self, data):
        request = self.context.get("request")
        if not request:
            return data

        user = request.user

        client = data.get("client")
        plan = data.get("plan")

        # 🔒 SUPERUSER puede todo
        if user.is_superuser:
            return data

        # 🔒 Usuario debe tener gym asignado
        if not user.gym:
            raise serializers.ValidationError(
                {"detail": "Usuario sin gimnasio asignado."}
            )

        # 🔒 Cliente debe pertenecer al gym del usuario
        if client and client.gym != user.gym:
            raise serializers.ValidationError(
                {"client": "Este cliente no pertenece a tu sucursal."}
            )

        # 🔒 Plan debe pertenecer al gym del usuario
        if plan and plan.gym != user.gym:
            raise serializers.ValidationError(
                {"plan": "Este plan no pertenece a tu sucursal."}
            )

        # 🔒 Solo ADMIN puede forzar operational_status
        if "operational_status" in data:
            if user.role != user.Roles.ADMIN:
                raise serializers.ValidationError(
                    {"operational_status": "No tienes permisos para forzar el estado de la membresía."}
                )

        return data

