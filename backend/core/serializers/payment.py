from rest_framework import serializers
from core.models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    membership_client_first_name = serializers.SerializerMethodField()
    membership_client_last_name = serializers.SerializerMethodField()
    membership_plan = serializers.SerializerMethodField()
    membership_balance = serializers.SerializerMethodField()
    membership_gym = serializers.SerializerMethodField()

    created_by_name = serializers.ReadOnlyField(source="created_by.username")
    payment_method_name = serializers.ReadOnlyField(source="payment_method.name")

    membership_start_date = serializers.SerializerMethodField()
    membership_end_date = serializers.SerializerMethodField()
    gym_name = serializers.ReadOnlyField(source="gym.name")
    client_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "membership",
            "membership_client_first_name",
            "membership_client_last_name",
            "membership_plan",
            "payment_method",
            "payment_method_name",
            "amount",
            "status",
            "payment_date",
            "notes",
            "created_by_name",
            "membership_balance",
            "reference_number",
            "membership_gym",
            "membership_start_date",
            "membership_end_date",
            "gym_name",
            "client_full_name",
        ]

        read_only_fields = ["id", "status", "payment_date", "created_by_name"]

    # ===============================
    # SAFE FIELDS (NO ROMPEN SI NULL)
    # ===============================

    def get_membership_client_first_name(self, obj):
        if obj.membership and obj.membership.client:
            return obj.membership.client.first_name
        return None

    def get_membership_client_last_name(self, obj):
        if obj.membership and obj.membership.client:
            return obj.membership.client.last_name
        return None

    def get_membership_plan(self, obj):
        if obj.membership and obj.membership.plan:
            return obj.membership.plan.name
        return None

    def get_membership_balance(self, obj):
        # Caja: saldo ACTUAL. VOID no muestra saldo.
        if obj.status == "VOID":
            return None
        if obj.membership:
            return obj.membership.balance
        return None

    def get_membership_gym(self, obj):
        if obj.membership and obj.membership.gym:
            return obj.membership.gym.id
        return None

    def get_membership_start_date(self, obj):
        if obj.membership:
            return obj.membership.start_date
        return None

    def get_membership_end_date(self, obj):
        if obj.membership:
            return obj.membership.end_date
        return None

    def get_client_full_name(self, obj):
        if obj.client:
            return f"{obj.client.first_name} {obj.client.last_name}"
        return None
    


    # ===============================
    # VALIDACIONES
    # ===============================

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del pago debe ser mayor a cero.")
        return value

    def validate(self, data):
        user = self.context['request'].user
        membership = data.get('membership')
        
        # Si no es SuperUser y no es Admin, validamos que sea de su sucursal
        if not user.is_superuser and user.role not in ['ADMIN', 'owner']: # Ajusta según tus roles
             if membership and hasattr(user, 'gym') and membership.gym != user.gym:
                raise serializers.ValidationError(
                    {"membership": "No puedes registrar pagos para otra sucursal."}
                )
        return data