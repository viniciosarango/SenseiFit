import phonenumbers
from rest_framework import serializers
from core.models.client import Client
from core.models.membership import Membership
from django.templatetags.static import static

class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    membership_info = serializers.SerializerMethodField()
    photo = serializers.ImageField(required=False, allow_null=True)
    photo_url = serializers.SerializerMethodField()

    gym_name = serializers.ReadOnlyField(source='gym.name')

    
    class Meta:
        model = Client
        fields = [
            'id', 'id_number', 'hikvision_id', 'first_name', 'last_name', 
            'full_name', 'email', 'phone', 'birth_date', 'gender', 
            'photo', 'photo_url', 'membership_info', 'created_at', 'gym_name',
        ]
        read_only_fields = [
            'id',
            'membership_info',
            'created_at',
        ]
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }





    def get_photo_url(self, obj):
        request = self.context.get('request')

        if obj.photo:
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        path = static('img/user-gym.png')
        if request:
            return request.build_absolute_uri(path)
        return path

    


    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


    def get_membership_info(self, obj):
        
        #membership = obj.memberships.filter(operational_status='ACTIVE', ).first()       
        membership = obj.memberships.filter(
            operational_status__in=['ACTIVE', 'SCHEDULED']
        ).order_by('-operational_status').first()

        if membership:
            return {
                "id": membership.id,
                "has_active": membership.operational_status == 'ACTIVE',
                "status": membership.operational_status,
                "plan_name": membership.plan.name,
                "financial_status": membership.financial_status,
                "balance": float(membership.balance), # Aseguramos formato numérico
                "due_date": membership.payment_due_date,
                "end_date": membership.end_date
            }
        return {"has_active": False, "message": "Sin Membresía Activa"}

    # --- VALIDACIONES PROFESIONALES ---


    def validate_phone(self, value):
        if not value:
            return value

        try:
            # Región por defecto Ecuador (puedes cambiarla dinámicamente después)
            parsed = phonenumbers.parse(value, "EC")

            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Número de teléfono inválido.")

            # Normalizamos a formato internacional E.164
            normalized = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )

            request = self.context.get("request")
            gym = getattr(request.user, "gym", None)
            queryset = Client.objects.filter(phone=normalized, gym=gym)

            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)

            if queryset.exists():
                raise serializers.ValidationError("Este número ya está registrado.")

            return normalized

        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Formato de número inválido.")
