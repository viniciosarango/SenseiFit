import phonenumbers
from django.core.exceptions import ValidationError
from rest_framework import serializers
from core.models.client import Client
from core.models.membership import Membership
from django.templatetags.static import static
from core.models.client_gym import ClientGym
from django.db.models import Sum, Q
from decimal import Decimal



class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    membership_info = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()
    photo = serializers.ImageField(required=False, allow_null=True)
    photo_url = serializers.SerializerMethodField()
    gyms = serializers.SerializerMethodField()


    
    class Meta:
        model = Client
        
        fields = [
            'id',
            'country',
            'document_type',
            'id_number',
            'hikvision_id',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'birth_date',
            'gender',
            'photo',
            'photo_url',
            'membership_info',
            'outstanding_balance',
            'created_at',
            'gyms',
            'is_active'
        ]
        
        read_only_fields = [
            'id',
            'membership_info',
            'created_at',
            'company',
            'user',
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

    def get_gyms(self, obj):
        return [
            {
                "id": link.gym.id,
                "name": link.gym.name
            }
            for link in obj.gym_links.select_related("gym").all()
        ]


    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    

    def get_outstanding_balance(self, obj):
        # Membresías activas o programadas (las que te importan para deuda)
        memberships = obj.memberships.filter(
            operational_status__in=['ACTIVE', 'SCHEDULED']
        )

        total_amount = memberships.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')

        total_paid = memberships.aggregate(
            paid=Sum('payments__amount', filter=Q(payments__status='PAID'))
        )['paid'] or Decimal('0.00')

        outstanding = total_amount - total_paid
        if outstanding < 0:
            outstanding = Decimal('0.00')

        return float(outstanding)


    def get_membership_info(self, obj):
        
        if not obj.is_active:
            return {"has_active": False, "message": "Cliente inactivo"}
        
        membership = obj.memberships.filter(
            operational_status__in=['ACTIVE', 'SCHEDULED'],
            balance__gt=0
        ).order_by('-created_at').first()

        # 2) Si no hay deuda, mostrar la más reciente ACTIVE/SCHEDULED
        if not membership:
            membership = obj.memberships.filter(
                operational_status__in=['ACTIVE', 'SCHEDULED']
            ).order_by('-created_at').first()

        if membership:
            return {
                "id": membership.id,
                "has_active": membership.operational_status == 'ACTIVE',
                "status": membership.operational_status,
                "plan_name": membership.plan.name,
                "financial_status": membership.financial_status,
                "balance": float(membership.balance),
                "due_date": membership.payment_due_date,
                "end_date": membership.end_date,
                "renovation_date": membership.renovation_date,
            }

        return {"has_active": False, "message": "Sin Membresía Activa"}

    # --- VALIDACIONES PROFESIONALES ---


    def validate_phone(self, value):
        if not value:
            return value

        text = str(value).strip()

        try:
            parsed = phonenumbers.parse(text, None)

            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Número telefónico inválido.")

            normalized = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )

            return normalized

        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(
                "Formato inválido. Use formato internacional. Ej: +593991122334"
            )


    def validate_id_number(self, value):
        if not value:
            return value

        text = str(value).strip()
        country = self.initial_data.get("country")
        document_type = self.initial_data.get("document_type")

        if not country:
            raise serializers.ValidationError("Debe especificar el país.")

        if not document_type:
            raise serializers.ValidationError("Debe especificar el tipo de documento.")

        # 🔹 Validación Ecuador
        if country == "EC" and document_type == "NATIONAL_ID":

            if not text.isdigit():
                raise serializers.ValidationError("La cédula ecuatoriana debe contener solo números.")

            if len(text) != 10:
                raise serializers.ValidationError("La cédula ecuatoriana debe tener 10 dígitos.")

            digits = [int(d) for d in text]

            province = int(text[:2])
            third = digits[2]

            if not (1 <= province <= 24 and third < 6):
                raise serializers.ValidationError("Cédula inválida (provincia o tercer dígito incorrecto).")

            total = 0
            for i in range(9):
                num = digits[i] * (2 if i % 2 == 0 else 1)
                if num > 9:
                    num -= 9
                total += num

            check_digit = (10 - (total % 10)) % 10

            if digits[9] != check_digit:
                raise serializers.ValidationError("Cédula inválida (dígito verificador incorrecto).")

            return text

        # 🔹 Otros países o pasaporte
        if 4 <= len(text) <= 30:
            return text

        raise serializers.ValidationError("Documento inválido.")