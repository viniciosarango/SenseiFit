from rest_framework import serializers
from core.models import Service

class ServiceSerializer(serializers.ModelSerializer):
    # 📖 LECTURA: El front recibe el nombre del gimnasio para confirmar el silo
    gym_name = serializers.ReadOnlyField(source='gym.name')

    class Meta:
        model = Service
        fields = [
            'id', 'gym', 'gym_name', 'name', 'description', 
            'price', 'is_active', 'created_at'
        ]
        
        # 🎯 EL CANDADO SAAS:
        # El gym es inmutable; el búnker lo asigna automáticamente.
        read_only_fields = ['id', 'gym', 'created_at']

    def validate_price(self, value):
        """
        Regla Financiera: No permitimos servicios con precio negativo.
        """
        if value < 0:
            raise serializers.ValidationError("El precio del servicio no puede ser negativo.")
        return value

    def validate_name(self, value):
        """
        Unicidad: Evitamos que una sucursal cree dos veces el mismo servicio.
        """
        user = self.context['request'].user
        
        # Buscamos si ya existe el nombre en TU gimnasio
        queryset = Service.objects.filter(gym=user.gym, name__iexact=value)
        
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
            
        if queryset.exists():
            raise serializers.ValidationError("Ya tienes un servicio registrado con este nombre.")
        return value