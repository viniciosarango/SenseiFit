from rest_framework import serializers
from core.models import PaymentMethod

class PaymentMethodSerializer(serializers.ModelSerializer):
    gym_name = serializers.ReadOnlyField(source='gym.name')

    class Meta:
        model = PaymentMethod
        fields = [
            'id',  'name', 'description', 'active',
            'created_at', 'gym', 'gym_name'
        ]
        
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        
        user = self.context['request'].user
        
        queryset = PaymentMethod.objects.filter(
            gym = self.initial_data.get("gym") or user.gym,
            name__iexact=value
        )
        
        # Si estamos editando, excluimos el registro actual
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
            
        if queryset.exists():
            raise serializers.ValidationError(
                "Ya tienes un método de pago con este nombre."
            )
        return value