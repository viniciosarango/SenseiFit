from rest_framework import serializers
from core.models import GymClass, Service, User

class GymClassSerializer(serializers.ModelSerializer):
    # 📖 Lectura: Para que el front pinte bonito sin peticiones extra
    service_name = serializers.ReadOnlyField(source='service.name')
    instructor_name = serializers.ReadOnlyField(source='instructor.full_name')
    
    # 📊 Lógica de Negocio: El backend calcula la disponibilidad
    spots_available = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()

    class Meta:
        model = GymClass
        fields = [
            'id', 'gym', 'service', 'service_name', 'instructor', 
            'instructor_name', 'day_of_week', 'start_time', 'end_time', 
            'capacity', 'spots_available', 'is_full'
        ]
        
        # 🎯 EL CANDADO: El gym es sagrado, se asigna en la vista.
        read_only_fields = ['id', 'gym']

    def get_spots_available(self, obj):
        # Aquí restaríamos las reservaciones actuales (cuando tengamos ese modelo)
        # Por ahora devolvemos la capacidad total o la lógica de reserva
        return obj.capacity # Ajustar cuando integremos Reservations

    def get_is_full(self, obj):
        return self.get_spots_available(obj) <= 0

    def validate(self, data):
        """
        VALIDACIÓN CRUZADA (Cross-check):
        Asegura que el servicio y el instructor pertenezcan al mismo gimnasio.
        """
        user = self.context['request'].user
        service = data.get('service')
        instructor = data.get('instructor')

        if not user.is_superuser:
            if service and service.gym != user.gym:
                raise serializers.ValidationError(
                    {"service": "Este servicio no está disponible en tu sucursal."}
                )
            if instructor and instructor.gym != user.gym:
                raise serializers.ValidationError(
                    {"instructor": "Este instructor no pertenece a tu sucursal."}
                )
        return data