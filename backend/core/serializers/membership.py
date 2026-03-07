from django.utils import timezone
from rest_framework import serializers
from core.models import Membership, ClientGym



class MembershipSerializer(serializers.ModelSerializer):
    
    client_name = serializers.CharField(source="client", read_only=True)
    client_id_number = serializers.ReadOnlyField(source="client.id_number")
    plan_name = serializers.ReadOnlyField(source="plan.name")
    plan_type = serializers.ReadOnlyField(source="plan.plan_type")
    gym_name = serializers.ReadOnlyField(source="gym.name")
    freeze_days_current = serializers.SerializerMethodField()

    paid_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        write_only=True,
        required=False,
        default=0
    )

    credit_days = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    payment_due_date = serializers.DateField(required=False, allow_null=True)  

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

    sale_type = serializers.ChoiceField(
        choices=["CASH", "CREDIT"],
        required=False,
        default="CASH"
    )    

    class Meta:
        model = Membership
        fields = [
            "id", "created_at",
            "client", "plan", "plan_id", "plan_name", "plan_type", "gym",
            "client_name", "client_id_number", "gym_name",
            "start_date", "requested_start_date", "end_date", "renovation_date", "payment_due_date",
            "original_price", "discount_percent_applied", "enrollment_fee_applied",
            "final_price", "total_amount", "paid_amount", "balance",
            "financial_status", "operational_status", "notes",
            "payment_method_id", "is_upgrade",
            "sessions_total", "sessions_consumed", "sessions_remaining",
            "courtesy_qty","freeze_start_date", "total_freeze_days",
            "freeze_days_current", "sale_type", "credit_days",
        ]

        read_only_fields = [
            "id", "gym", "start_date", "end_date", "renovation_date",
            "original_price", "final_price", "total_amount", "balance",
            "financial_status", "plan", "sessions_remaining"
        ]


    def get_freeze_days_current(self, obj):
        if obj.operational_status == "FROZEN" and obj.freeze_start_date:
            today = timezone.localdate()
            return (today - obj.freeze_start_date).days + obj.total_freeze_days
        return obj.total_freeze_days


    def validate(self, data):
        request = self.context.get("request")
        if not request:
            return data

        user = request.user

        if "operational_status" in data:
            if not user.is_superuser and user.role != user.Roles.ADMIN:
                raise serializers.ValidationError(
                    {"operational_status": "No tienes permisos para forzar el estado de la membresía."}
                )

        sale_type = data.get("sale_type", "CASH")
        credit_days = data.get("credit_days")
        payment_due_date = data.get("payment_due_date")

        if sale_type == "CASH":
            if credit_days is not None or payment_due_date is not None:
                raise serializers.ValidationError(
                    {"sale_type": "Una venta CASH no acepta plazo ni fecha límite de pago."}
                )

        elif sale_type == "CREDIT":
            if payment_due_date is not None:
                from django.utils import timezone
                if payment_due_date <= timezone.localdate():
                    raise serializers.ValidationError(
                        {"payment_due_date": "La fecha límite debe ser posterior a hoy."}
                    )

            if credit_days is not None and int(credit_days) <= 0:
                raise serializers.ValidationError(
                    {"credit_days": "Debe ser mayor a 0."}
                )

            if credit_days is not None and payment_due_date is not None:
                raise serializers.ValidationError(
                    {"payment_due_date": "Envía credit_days o payment_due_date, pero no ambos."}
                )

        return data    
    


class MembershipHistorySerializer(MembershipSerializer):
    payments = serializers.SerializerMethodField()

    class Meta(MembershipSerializer.Meta):
        # Heredamos todos los campos del anterior y añadimos 'payments'
        fields = MembershipSerializer.Meta.fields + ['payments']

    def get_payments(self, obj):
        # Importamos AQUÍ adentro para evitar el error de importación circular
        from core.serializers.payment import PaymentSerializer
        
        # Intentamos obtener los pagos. 
        # Si 'payment_set' falla, probamos con 'payments' (según tu related_name)
        try:
            return PaymentSerializer(obj.payment_set.all(), many=True).data
        except AttributeError:
            return PaymentSerializer(obj.payments.all(), many=True).data