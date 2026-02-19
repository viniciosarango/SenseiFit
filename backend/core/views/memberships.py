# TestDeploy2


from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from core.models import Membership
from core.serializers import MembershipSerializer
from core.services.memberships import create_membership_service, MembershipError, cancel_membership_service
from core.services.payments import register_payment
from .base import CompanyGymScopedViewSet


class MembershipViewSet(CompanyGymScopedViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # 🔴 CLIENT → solo sus propias membresías
        if user.role == user.Roles.CLIENT:
            return Membership.objects.filter(
                client__user=user
            ).select_related('client', 'plan').order_by('-created_at')

        # 🟢 ADMIN / STAFF / SUPERUSER → usar blindaje base
        queryset = super().get_queryset()

        # Filtros opcionales por URL
        f_status = self.request.query_params.get('financial_status')
        o_status = self.request.query_params.get('operational_status')

        if f_status:
            queryset = queryset.filter(financial_status__in=f_status.split(','))

        if o_status:
            queryset = queryset.filter(operational_status=o_status)

        return queryset.select_related('client', 'plan').order_by('-created_at')









    def create(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = self.request.user
        data = serializer.validated_data

        if not user.is_superuser:
            if data['client'].gym != user.gym or data['plan'].gym != user.gym:
                raise ValidationError("El cliente o el plan no pertenecen a tu sucursal.")

        try:
            # Delegamos la "magia" al servicio que ya tienes
            membership = create_membership_service(
                gym=user.gym,
                client=data['client'],
                plan_id=data['plan_id'],

                requested_start_date=data.get('requested_start_date'),            
                #requested_start_date=data.get('start_date', timezone.now().date()),
                
                created_by=user,                
                discount_percent=data.get('discount_percent_applied', 0),
                paid_amount=data.get('paid_amount', 0),
                payment_method_id=data.get('payment_method_id'),
                #is_upgrade=data.get('is_upgrade', False), # El nuevo interruptor
                notes=data.get('notes', ""),
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