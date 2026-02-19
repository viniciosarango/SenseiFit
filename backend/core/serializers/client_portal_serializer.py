from rest_framework import serializers
from core.models import Client


class ClientPortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "phone",
            "email",
            "birth_date",
            "photo",
        ]

    def validate_email(self, value):
        if value:
            value = value.strip().lower()

            # Validar unicidad solo si se está cambiando
            client_id = self.instance.id if self.instance else None

            if Client.objects.filter(email=value).exclude(id=client_id).exists():
                raise serializers.ValidationError(
                    "Este email ya está registrado en otro cliente."
                )

        return value
