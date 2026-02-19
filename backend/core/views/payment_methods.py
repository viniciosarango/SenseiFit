from rest_framework import permissions
from core.models import PaymentMethod
from core.serializers import PaymentMethodSerializer
from .base import CompanyGymScopedViewSet
from rest_framework.exceptions import PermissionDenied



class PaymentMethodViewSet(CompanyGymScopedViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        ASIGNACIÓN AUTOMÁTICA:
        El método de pago queda vinculado al gimnasio del usuario.
        """
        user = self.request.user

        if not user.is_superuser and not user.gym:
            raise PermissionDenied("Usuario sin gimnasio asignado.")

        serializer.save(
            gym=user.gym if not user.is_superuser else serializer.validated_data.get("gym")
        )
