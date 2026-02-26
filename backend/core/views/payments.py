from django.conf import settings
from django.db import transaction
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Payment, Membership, PaymentMethod
from core.serializers import PaymentSerializer
from core.services.payments import register_payment, void_payment
from .base import CompanyGymScopedViewSet


class PaymentViewSet(CompanyGymScopedViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    

    def get_queryset(self):
        queryset = super().get_queryset().select_related("membership")

        membership_id = self.request.query_params.get('membership_id')
        if membership_id:
            queryset = queryset.filter(membership_id=membership_id)

        return queryset.order_by('-payment_date')



    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        data = serializer.validated_data

        # 🛑 FILTRO DE SEGURIDAD SAAS
        # Validamos que la membresía sea de este gimnasio antes de cobrar
        membership = data['membership']
        if not user.is_superuser and membership.gym != user.gym:
            return Response(
                {"detail": "No puedes registrar pagos en membresías ajenas."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # 💸 Llamada al motor de pagos (Tu Servicio)
            payment, _ = register_payment(
                membership_id=membership.id,
                amount=data['amount'],
                payment_method_id=data['payment_method'].id,
                notes=request.data.get("notes", ""),
                created_by=user,
            )

            # Devolvemos el pago serializado
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
            import inspect
            real_fn = inspect.unwrap(void_payment)
            print("VOID_PAYMENT_MODULE:", void_payment.__module__)
            print("VOID_PAYMENT_REAL_FROM:", inspect.getsourcefile(real_fn))
            print("VOID_PAYMENT_REAL_NAME:", real_fn.__name__)

            
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