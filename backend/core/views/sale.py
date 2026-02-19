from rest_framework import permissions, serializers
from rest_framework.exceptions import PermissionDenied

from core.models import Sale
from core.serializers import SaleSerializer
from .base import CompanyGymScopedViewSet


class SaleViewSet(CompanyGymScopedViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-sale_date')

    def perform_create(self, serializer):
        user = self.request.user
        product = serializer.validated_data.get('product')

        if not user.is_superuser and not user.gym:
            raise PermissionDenied("Usuario sin gimnasio asignado.")

        # Validación de seguridad multi-tenant
        if not user.is_superuser and product.gym != user.gym:
            raise serializers.ValidationError(
                "Seguridad: No puedes vender un producto que no pertenece a tu catálogo."
            )

        serializer.save(
            gym=user.gym if not user.is_superuser else serializer.validated_data.get("gym")
        )
