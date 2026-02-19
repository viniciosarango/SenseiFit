from rest_framework import serializers
from core.models import Gym

class GymSerializer(serializers.ModelSerializer):
    # 🏢 Información de la empresa madre (Solo lectura)
    company_name = serializers.ReadOnlyField(source='company.name')
    
    # 📊 Estadísticas rápidas: El backend piensa, el front solo pinta
    total_clients = serializers.IntegerField(
        source='client_set.count', 
        read_only=True
    )
    active_memberships_count = serializers.SerializerMethodField()

    class Meta:
        model = Gym
        fields = [
            'id', 'company', 'company_name', 'name', 'address', 
            'phone', 'is_active', 'total_clients', 
            'active_memberships_count', 'created_at'
        ]
        
        # 🎯 BLOQUEO MAESTRO:
        # El usuario no elige a qué 'company' pertenece el gym.
        # Eso lo decide el backend en la View.
        read_only_fields = ['id', 'company', 'created_at']

    def get_active_memberships_count(self, obj):
        """
        Calcula cuántas membresías están actualmente activas en esta sucursal.
        """
        return obj.membership_set.filter(operational_status="ACTIVE").count()

    def validate_name(self, value):
        """
        Regla de negocio: No pueden haber dos sucursales con el mismo nombre 
        dentro de la misma empresa (ej. 'Sucursal Norte').
        """
        user = self.context['request'].user
        if Gym.objects.filter(company=user.company, name__iexact=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                "Ya tienes una sucursal registrada con este nombre."
            )
        return value