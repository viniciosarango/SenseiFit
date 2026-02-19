from rest_framework import serializers
from core.models import Attendance, Client

class AttendanceSerializer(serializers.ModelSerializer):
    # Usamos PrimaryKeyRelatedField para que el frontend pueda enviar el ID del cliente
    # Pero lo limitamos: solo clientes que el usuario pueda ver (esto se refuerza en la vista)
    client_name = serializers.ReadOnlyField(source='client.full_name') # Para mostrar en el front
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'client', 'client_name', 'gym', 'check_in_time', 
            'is_allowed', 'denial_reason'
        ]
        
        # 🎯 REGLA DE ORO DEL BÚNKER:
        # El gym y el tiempo de entrada no los decide el cliente, los dicta el servidor.
        read_only_fields = ['gym', 'check_in_time', 'is_allowed', 'denial_reason']

    def validate_client(self, value):
        """
        Validación de seguridad: ¿El cliente pertenece al mismo gimnasio 
        que el usuario que registra la asistencia?
        """
        user = self.context['request'].user
        if not user.is_superuser and value.gym != user.gym:
            raise serializers.ValidationError(
                "Seguridad: Este cliente no pertenece a tu sucursal."
            )
        return value