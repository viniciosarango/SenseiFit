from rest_framework import serializers
from core.models import Plan

class PlanSerializer(serializers.ModelSerializer):

    gym_name = serializers.CharField(source='gym.name', read_only=True)


    plan_type = serializers.ChoiceField(
        choices=Plan.PLAN_TYPES,
        required=False,
        default='TIME'
    )

    active_subscriptions = serializers.IntegerField(
        source='membership_set.count',
        read_only=True
    )

    class Meta:
        model = Plan
        fields = [
            'id', 'gym', 'gym_name', 'name', 'code', 'description',
            'plan_type', 
            'price', 'duration_days', 'is_active', 
            'active_subscriptions', 'created_at',
            'total_sessions',
        ]
        
        read_only_fields = ['id', 'gym_name', 'gym', 'created_at']


    def validate_code(self, value):
        """
        🛡️ El Escudo Pro: Limpia espacios en blanco y maneja nulos.
        Un código de plan debe ser único o nulo, nunca una cadena vacía.
        """
        if value:
            value = value.strip()
            if value == "":
                return None
        return value


    def validate_price(self, value):
        """
        Regla Financiera: No existen planes de costo cero o negativos 
        (a menos que sean cortesías, pero eso va en otro modelo).
        """
        if value <= 0:
            raise serializers.ValidationError("El precio del plan debe ser mayor a cero.")
        return value


    def validate_duration_days(self, value):
        """
        Regla de Tiempo: Un plan debe durar al menos un día.
        """
        if value < 1:
            raise serializers.ValidationError("La duración mínima es de 1 día.")
        return value


    def validate(self, data):
        plan_type = data.get(
            "plan_type",
            self.instance.plan_type if self.instance else None
        )

        total_sessions = data.get(
            "total_sessions",
            self.instance.total_sessions if self.instance else 0
        )

        if plan_type == "SESSIONS" and total_sessions <= 0:
            raise serializers.ValidationError(
                {"total_sessions": "Debes indicar el número de sesiones."}
            )

        return data
    


