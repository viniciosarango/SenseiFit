from django.conf import settings
from django.db import transaction
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Payment, Membership, PaymentMethod
from core.serializers import PaymentSerializer
from core.services.payments import register_payment, void_payment, PaymentError
from .base import CompanyGymScopedViewSet


class PaymentViewSet(CompanyGymScopedViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    

    def get_queryset(self):
        queryset = super().get_queryset()

        membership_id = self.request.query_params.get('membership_id')
        if membership_id:
            queryset = queryset.filter(membership_id=membership_id)

        # ✅ Filtro: status=PAID | VOID
        status_param = self.request.query_params.get('status')
        if status_param in ['PAID', 'VOID']:
            queryset = queryset.filter(status=status_param)

        # ✅ Por defecto NO mostrar anulados, a menos que include_void=1
        include_void = self.request.query_params.get('include_void')
        if include_void not in ['1', 'true', 'True']:
            queryset = queryset.exclude(status='VOID')

        return queryset.order_by('-payment_date')


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data
        membership = data["membership"]

        # 🛑 FILTRO DE SEGURIDAD SAAS (por rol)
        # SUPERUSER: libre
        if user.is_superuser:
            pass

        # ADMIN: cualquier gym de su company
        elif user.role == user.Roles.ADMIN:
            if not user.company or membership.gym.company_id != user.company_id:
                return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        # STAFF: solo su gym
        elif user.role == user.Roles.STAFF:
            if not user.gym or membership.gym_id != user.gym_id:
                return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        else:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # 💸 Llamada al motor de pagos
            payment, _ = register_payment(
                membership_id=membership.id,
                amount=data["amount"],
                payment_method_id=data["payment_method"].id,
                notes=request.data.get("notes", ""),
                created_by=user,
            )

            response_serializer = self.get_serializer(payment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except PaymentError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):

        payment = self.get_object()
        user = request.user
        razon = request.data.get("razon")
        pin = request.data.get("pin")

        if not razon:
            return Response(
                {"detail": "Debe indicar el motivo de la anulación."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔐 VALIDACIÓN DE PIN SOLO PARA STAFF
        if user.role == user.Roles.STAFF:
            if not pin:
                return Response(
                    {"detail": "PIN requerido para anular pagos."},
                    status=status.HTTP_403_FORBIDDEN
                )

            if pin != settings.CANCEL_PIN:
                return Response(
                    {"detail": "PIN incorrecto."},
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            void_payment(payment_id=payment.id, reason=razon, user=user)
            return Response(
                {"detail": "Pago anulado y saldo restaurado."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )