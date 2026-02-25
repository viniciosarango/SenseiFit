from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from core.models import Membership, ClientGym, Gym, Company
from core.serializers.membership import MembershipSerializer, MembershipHistorySerializer
from core.services.memberships import create_membership_service, MembershipError, cancel_membership_service
from core.services.payments import register_payment
from .base import CompanyGymScopedViewSet
from core.services.memberships import activate_membership_now
from core.services.memberships import (
    freeze_membership_service,
    unfreeze_membership_service
)


class MembershipViewSet(CompanyGymScopedViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        client_id = self.request.query_params.get('client_id')
        f_status = self.request.query_params.get('financial_status')
        o_status = self.request.query_params.get('operational_status')

        if client_id:
            queryset = queryset.filter(client_id=client_id)

        if f_status:
            queryset = queryset.filter(financial_status__in=f_status.split(','))

        if o_status:
            queryset = queryset.filter(operational_status=o_status)

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
            financial_status__in=['pending', 'partial']
        )
        serializer = MembershipSerializer(queryset, many=True)
        return Response(serializer.data)



    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        client = data["client"]
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
            membership = create_membership_service(
                gym=gym,
                client=client,
                plan_id=plan_id,
                requested_start_date=data.get("requested_start_date"),
                created_by=user,
                discount_percent=data.get("discount_percent_applied", 0),
                paid_amount=data.get("paid_amount", 0),
                payment_method_id=data.get("payment_method_id"),
                notes=data.get("notes", ""),
                force_operational_status=data.get("operational_status"),
            )

            response_serializer = self.get_serializer(membership)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

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
                set_due_days=request.data.get('set_due_days'),
                created_by=request.user if request.user.is_authenticated else None
            )
            
            serializer = self.get_serializer(updated_membership)
            return Response(serializer.data)
            
        except Exception as e:
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

            serializer = self.get_serializer(updated)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except MembershipError as e:
            raise ValidationError({"detail": str(e)})


    @action(detail=True, methods=["post"], url_path="freeze")
    def freeze(self, request, pk=None):
        membership = self.get_object()

        try:
            updated = freeze_membership_service(
                membership=membership,
                requested_by=request.user
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
        


    @action(detail=True, methods=["post"], url_path="freeze")
    def freeze(self, request, pk=None):
        membership = self.get_object()
        pin = request.data.get("pin")

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
        
