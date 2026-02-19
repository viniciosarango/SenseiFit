from rest_framework import serializers
from core.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    
    membership_client = serializers.ReadOnlyField(source="membership.client.full_name")

    membership_client_first_name = serializers.ReadOnlyField(source="membership.client.first_name")
    membership_client_last_name = serializers.ReadOnlyField(source="membership.client.last_name")

    membership_plan = serializers.ReadOnlyField(source="membership.plan.name")
    membership_balance = serializers.ReadOnlyField(source="membership.balance")
    created_by_name = serializers.ReadOnlyField(source="created_by.username")
    payment_method_name = serializers.ReadOnlyField(source="payment_method.name")
    
    class Meta:
        model = Payment
        fields = [
            "id", "membership", "membership_client", "membership_client_first_name", 
            "membership_client_last_name",
            "membership_plan",
            "payment_method", "payment_method_name",
            "amount", "status", 'payment_date', "notes", "created_by_name",
            "membership_balance", "reference_number",
        ]
        
        read_only_fields = ["id", "status", "payment_date", "created_by_name"]

    def validate_amount(self, value):
        """
        El dinero no puede ser negativo ni cero.
        """
        if value <= 0:
            raise serializers.ValidationError("El monto del pago debe ser mayor a cero.")
        return value

    def validate(self, data):
        """
        VALIDACIÓN DE SILO:
        Aseguramos que la membresía y el método de pago 
        pertenezcan al gimnasio del usuario que registra.
        """
        user = self.context['request'].user
        membership = data.get('membership')
        payment_method = data.get('payment_method')

        if not user.is_superuser:
            if membership.gym != user.gym:
                raise serializers.ValidationError(
                    {"membership": "No puedes registrar pagos para una membresía de otra sucursal."}
                )
            if payment_method.gym != user.gym:
                raise serializers.ValidationError(
                    {"payment_method": "Este método de pago no pertenece a tu sucursal."}
                )
        
        return data