from rest_framework.decorators import action
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from datetime import timedelta

from core.utils.hikvision import sync_hikvision_async

from django.utils import timezone

from core.models import Membership, ClientGym, Gym, Company
from core.serializers.membership import MembershipSerializer, MembershipHistorySerializer

from core.services.memberships import (
    create_membership_service,
    cancel_membership_service,
    activate_membership_now,
    freeze_membership_service,
    unfreeze_membership_service,
    upgrade_membership_service,
    MembershipError,
)

from core.services.payments import register_payment, PaymentError

from .base import CompanyGymScopedViewSet



class MembershipViewSet(CompanyGymScopedViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        client_id = self.request.query_params.get('client_id')
        f_status = self.request.query_params.get('financial_status')
        o_status = self.request.query_params.get('operational_status')
        expiry_filter = self.request.query_params.get('expiry_filter')        

        if client_id:
            queryset = queryset.filter(client_id=client_id)

        if f_status:
            queryset = queryset.filter(financial_status__in=f_status.split(','))

        if o_status:
            queryset = queryset.filter(operational_status__in=o_status.split(','))

        today = timezone.localdate()

        if expiry_filter == "today":
            queryset = queryset.filter(
                operational_status="ACTIVE",
                end_date=today
            )

        elif expiry_filter == "next_3_days":
            queryset = queryset.filter(
                operational_status="ACTIVE",
                end_date__gt=today,
                end_date__lte=today + timedelta(days=3)
            )

        return queryset.select_related('client', 'plan').order_by('-created_at')
    

    @action(detail=False, methods=['get'], url_path='historial-cliente')
    def historial_cliente(self, request):
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response({"detail": "Falta client_id"}, status=400)
            
        queryset = self.get_queryset().filter(client_id=client_id)
        serializer = MembershipHistorySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='por-cobrar-cliente')
    def por_cobrar_cliente(self, request):
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response({"detail": "Falta client_id"}, status=400)
            
        queryset = self.get_queryset().filter(
            client_id=client_id, 
            financial_status__in=['PENDING', 'PARTIAL']            
        )
        serializer = MembershipSerializer(queryset, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=["post"], url_path="sync-hikvision-bulk")
    def sync_hikvision_bulk(self, request):
        queryset = self.get_queryset().filter(
            operational_status__in=["ACTIVE", "SCHEDULED"]
        ).select_related("client")

        total = 0
        synced = 0
        skipped = 0
        failed = 0
        errors = []

        for membership in queryset:
            total += 1

            client = membership.client
            if not client or not client.hikvision_id:
                skipped += 1
                continue

            if not membership.start_date or not membership.end_date:
                skipped += 1
                continue

            ok, message = sync_hikvision_async(membership)
            if ok:
                synced += 1
            else:
                failed += 1
                errors.append({
                    "membership_id": membership.id,
                    "client_name": getattr(client, "full_name", str(client)),
                    "hikvision_id": client.hikvision_id,
                    "error": message,
                })

        return Response(
            {
                "detail": "Sincronización masiva finalizada",
                "total": total,
                "synced": synced,
                "skipped": skipped,
                "failed": failed,
                "errors": errors[:20],
            },
            status=status.HTTP_200_OK
        )


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data
        client = data["client"]

        # STAFF: venta a crédito requiere PIN
        if user.role == user.Roles.STAFF:
            sale_type = request.data.get("sale_type", "CASH")

            if sale_type == "CREDIT":
                from django.conf import settings
                pin = request.data.get("pin")
                if not pin or str(pin) != str(getattr(settings, "CANCEL_PIN", "")):
                    raise ValidationError({"pin": "PIN requerido o incorrecto para venta a crédito."})        

        if not client.is_active:
            raise ValidationError({"client": "Cliente inactivo. Debe reactivarse antes de vender una membresía."})
        
        plan_id = data["plan_id"]

        # 1) Resolver gym según rol (NUEVA ARQUITECTURA)
        if user.is_superuser:
            company_id = request.data.get("company")
            gym_id = request.data.get("gym")

            if not company_id:
                raise ValidationError({"detail": "Debe especificar la empresa."})
            if not gym_id:
                raise ValidationError({"detail": "Debe especificar el gimnasio."})

            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                raise ValidationError({"detail": "Empresa inválida."})

            try:
                gym = Gym.objects.get(id=gym_id, company=company)
            except Gym.DoesNotExist:
                raise ValidationError({"detail": "Gimnasio inválido para esta empresa."})

        elif user.role == user.Roles.ADMIN:
            if not user.company:
                raise ValidationError({"detail": "Usuario ADMIN sin empresa asignada."})

            gym_id = request.data.get("gym")
            if not gym_id:
                raise ValidationError({"detail": "Debe especificar el gimnasio."})

            try:
                gym = Gym.objects.get(id=gym_id, company=user.company)
            except Gym.DoesNotExist:
                raise ValidationError({"detail": "Gimnasio inválido para tu empresa."})

        elif user.role == user.Roles.STAFF:
            if not user.gym:
                raise ValidationError({"detail": "Usuario STAFF sin gimnasio asignado."})
            gym = user.gym

        else:
            raise ValidationError({"detail": "No tienes permiso para crear membresías."})

        # Seguridad multi-tenant: cliente debe pertenecer a la misma company del gym
        if client.company_id != gym.company_id:
            raise ValidationError({"client": "El cliente no pertenece a esta empresa."})
        
        # 2) Validar que el cliente esté vinculado al gym vía ClientGym
        if not ClientGym.objects.filter(client=client, gym=gym).exists():
            raise ValidationError({"client": "Este cliente no pertenece a esta sucursal."})

        # 3) Dejar que el servicio haga su magia
        try:
            sale_type = data.get("sale_type", "CASH")
            paid_amount = data.get("paid_amount", 0) or 0

            if sale_type == "CASH" and not data.get("payment_method_id"):
                raise ValidationError({"payment_method_id": "Debe seleccionar método de pago para una venta CASH."})

            if paid_amount > 0 and not data.get("payment_method_id"):
                raise ValidationError({"payment_method_id": "Debe seleccionar método de pago cuando exista abono inicial."})            
            
            membership = create_membership_service(
                gym=gym,
                client=client,
                plan_id=plan_id,
                requested_start_date=data.get("requested_start_date"),
                created_by=user,
                discount_percent=data.get("discount_percent_applied", 0),
                enrollment_fee=data.get("enrollment_fee_applied", 0),
                paid_amount=data.get("paid_amount", 0),
                payment_method_id=data.get("payment_method_id"),
                notes=data.get("notes", ""),
                force_operational_status=data.get("operational_status"),
                sale_type=sale_type,
                payment_due_date=data.get("payment_due_date"),
                credit_days=data.get("credit_days"),
            )

            response_serializer = self.get_serializer(membership)

            response_data = {
                **response_serializer.data,
                "hikvision_attempted": getattr(membership, "hikvision_attempted", False),
                "hikvision_synced": getattr(membership, "hikvision_synced", False),
                "hikvision_message": getattr(membership, "hikvision_message", ""),
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except MembershipError as e:
            raise ValidationError({"detail": str(e)})



    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):   
        membership = self.get_object()
        
        try:
            payment, updated_membership = register_payment(
                membership_id=membership.id,
                amount=request.data.get('amount'),
                payment_method_id=request.data.get('payment_method_id'),
                notes=request.data.get('notes', ""),
                created_by=request.user if request.user.is_authenticated else None
            )
            
            serializer = self.get_serializer(updated_membership)
            return Response(serializer.data)
            
        except PaymentError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)        


    #CANCELAR MEMBRESIA    
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        membership = self.get_object()
        pin = request.data.get("pin")
        reason = request.data.get("reason", "")

        try:
            cancel_membership_service(
                membership=membership,
                requested_by=request.user,
                pin=pin,
                reason=reason,
            )
            return Response({"detail": "Membresía cancelada."}, status=status.HTTP_200_OK)
        except MembershipError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

     
        
    @action(detail=True, methods=["post"], url_path="activate-now")
    def activate_now(self, request, pk=None):
        membership = self.get_object()

        try:
            updated = activate_membership_now(
                membership=membership,
                activated_by=request.user
            )

            if updated.client.hikvision_id and updated.start_date and updated.end_date:
                sync_hikvision_async(updated)

            serializer = self.get_serializer(updated)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except MembershipError as e:
            raise ValidationError({"detail": str(e)})


    @action(detail=True, methods=["post"], url_path="freeze")
    def freeze(self, request, pk=None):
        membership = self.get_object()

        pin = request.data.get("pin")
        if not pin:
            raise ValidationError({"detail": "Debe ingresar PIN."})

        try:
            updated = freeze_membership_service(
                membership=membership,
                requested_by=request.user,
                pin=pin
            )

            serializer = self.get_serializer(updated)
            return Response(serializer.data)

        except MembershipError as e:
            raise ValidationError({"detail": str(e)})
        

    @action(detail=True, methods=["post"], url_path="unfreeze")
    def unfreeze(self, request, pk=None):
        membership = self.get_object()

        pin = request.data.get("pin")
        if not pin:
            raise ValidationError({"detail": "Debe ingresar PIN."})

        try:
            updated = unfreeze_membership_service(
                membership=membership,
                requested_by=request.user,
                pin=pin
            )

            serializer = self.get_serializer(updated)
            return Response(serializer.data)

        except MembershipError as e:
            raise ValidationError({"detail": str(e)})
        

    @action(detail=True, methods=["post"], url_path="upgrade")
    def upgrade(self, request, pk=None):
        membership = self.get_object()

        new_plan_id = request.data.get("plan_id")
        payment_method_id = request.data.get("payment_method_id")
        paid_amount = request.data.get("paid_amount", 0)
        sale_type = request.data.get("sale_type", "CASH")
        notes = request.data.get("notes", "Upgrade de membresía")

        if not new_plan_id:
            raise ValidationError({"plan_id": "Debe indicar el plan destino para el upgrade."})

        try:
            upgraded = upgrade_membership_service(
                client=membership.client,
                gym=membership.gym,
                new_plan_id=new_plan_id,
                payment_method_id=payment_method_id,
                created_by=request.user,
                notes=notes,
                paid_amount=paid_amount,
                sale_type=sale_type,
            )

            serializer = self.get_serializer(upgraded)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except MembershipError as e:
            raise ValidationError({"detail": str(e)})
        

    @action(detail=True, methods=["post"], url_path="edit-scheduled")
    def edit_scheduled(self, request, pk=None):
        membership = self.get_object()

        if membership.operational_status != "SCHEDULED":
            raise ValidationError({"detail": "Solo se pueden editar membresías programadas."})

        pin = request.data.get("pin")
        if not pin:
            raise ValidationError({"detail": "Debe ingresar PIN."})

        from django.conf import settings
        if str(pin) != str(getattr(settings, "CANCEL_PIN", "")):
            raise ValidationError({"detail": "PIN incorrecto."})

        new_start_date = request.data.get("start_date")
        notes = request.data.get("notes", membership.notes or "")

        if not new_start_date:
            raise ValidationError({"start_date": "Debe indicar una nueva fecha de inicio."})

        from datetime import datetime, timedelta

        try:
            parsed_start = datetime.strptime(new_start_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError({"start_date": "Formato inválido. Use YYYY-MM-DD."})

        membership.start_date = parsed_start
        membership.end_date = parsed_start + timedelta(days=membership.plan.duration_days - 1)
        membership.notes = notes
        membership.save()

        serializer = self.get_serializer(membership)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=["post"], url_path="sync-hikvision")
    def sync_hikvision(self, request, pk=None):
        membership = self.get_object()
        client = membership.client

        if not client.hikvision_id:
            raise ValidationError({"detail": "El cliente no tiene hikvision_id configurado."})

        if not membership.start_date or not membership.end_date:
            raise ValidationError({"detail": "La membresía no tiene fechas válidas para sincronizar."})

        ok, message = sync_hikvision_async(membership)

        if ok:
            serializer = self.get_serializer(membership)
            return Response(
                {
                    "detail": message,
                    "membership": serializer.data,
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {"detail": message},
            status=status.HTTP_400_BAD_REQUEST
        )