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
        
        read_only_fields = ['id', 'gym', 'created_at']

    def validate_name(self, value):
        """
        Regla de Oro: No duplicar nombres de métodos de pago 
        dentro de la misma sucursal.
        """
        user = self.context['request'].user
        
        # Buscamos si ya existe ese nombre para TU gimnasio
        queryset = PaymentMethod.objects.filter(
            gym=user.gym, 
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