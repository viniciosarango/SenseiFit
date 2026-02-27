from rest_framework import serializers
from core.models import Client, Membership, Payment


class ClientPortalSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    membership_info = serializers.SerializerMethodField()
    memberships = serializers.SerializerMethodField()

    # ✅ NUEVO
    payments = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            # Identidad (solo lectura)
            "id",
            "full_name",
            "id_number",
            "hikvision_id",

            # Perfil editable
            "phone",
            "email",
            "birth_date",
            "photo",
            "photo_url",

            # Info para el portal
            "membership_info",
            "memberships",

            # ✅ NUEVO
            "payments",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "id_number",
            "hikvision_id",
            "photo_url",
            "membership_info",
            "memberships",
            "payments",
        ]

    def get_photo_url(self, obj):
        request = self.context.get("request")
        if obj.photo and hasattr(obj.photo, "url"):
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return request.build_absolute_uri("/static/img/user-gym.png") if request else "/static/img/user-gym.png"

    def get_membership_info(self, obj):
        m = (
            Membership.objects.filter(client=obj, operational_status="ACTIVE")
            .order_by("-start_date")
            .first()
        )

        if not m:
            m = (
                Membership.objects.filter(client=obj, operational_status="SCHEDULED")
                .order_by("start_date")
                .first()
            )

        if not m:
            return {"has_active": False, "message": "Sin Membresía Activa"}

        return {
            "id": m.id,
            "has_active": m.operational_status == "ACTIVE",
            "status": m.operational_status,
            "plan_name": (m.plan.name if m.plan else None),
            "financial_status": m.financial_status,
            "balance": float(m.balance),
            "due_date": m.payment_due_date,
            "end_date": m.end_date,
            "gym_name": (m.gym.name if m.gym else None),
            "sale_type": getattr(m, "sale_type", None),
        }

    def get_memberships(self, obj):
        qs = Membership.objects.filter(client=obj).order_by("-start_date")
        return [
            {
                "id": m.id,
                "plan_name": (m.plan.name if m.plan else None),
                "operational_status": m.operational_status,
                "financial_status": m.financial_status,
                "start_date": m.start_date,
                "end_date": m.end_date,
                "payment_due_date": m.payment_due_date,
                "total_amount": str(m.total_amount),
                "balance": str(m.balance),
                "gym_name": (m.gym.name if m.gym else None),
                "sale_type": getattr(m, "sale_type", None),
            }
            for m in qs
        ]

    # ✅ NUEVO: historial de pagos del cliente (por sus memberships)
    def get_payments(self, obj):
        request = self.context.get("request")

        # Por defecto: SOLO PAID (más limpio para cliente)
        include_void = False
        if request:
            include_void = str(request.query_params.get("include_void", "")).strip() in ("1", "true", "True")

        qs = Payment.objects.filter(client=obj).select_related("payment_method", "gym", "membership")

        if not include_void:
            qs = qs.filter(status="PAID")

        qs = qs.order_by("-payment_date")[:200]  # límite duro para portal (evita payload enorme)

        return [
            {
                "id": p.id,
                "membership_id": p.membership_id,
                "amount": str(p.amount),
                "status": p.status,
                "payment_date": p.payment_date,
                "payment_method_name": (p.payment_method.name if p.payment_method else None),
                "gym_name": (p.gym.name if p.gym else None),
                "reference_number": p.reference_number,
                "notes": p.notes,
                # útiles para UI (sin depender de PaymentSerializer pesado)
                "membership_plan": (p.membership.plan.name if p.membership and p.membership.plan else None),
                "membership_start_date": (p.membership.start_date if p.membership else None),
                "membership_end_date": (p.membership.end_date if p.membership else None),
            }
            for p in qs
        ]

    def validate_email(self, value):
        if value:
            value = value.strip().lower()
            client_id = self.instance.id if self.instance else None
            if Client.objects.filter(email=value).exclude(id=client_id).exists():
                raise serializers.ValidationError("Este email ya está registrado en otro cliente.")
        return value