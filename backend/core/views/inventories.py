from rest_framework import permissions, serializers
from rest_framework.exceptions import PermissionDenied

from core.models import Inventory
from core.serializers import InventorySerializer
from .base import CompanyGymScopedViewSet


class InventoryViewSet(CompanyGymScopedViewSet):
    queryset = Inventory.objects.select_related("product")
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset

        if user.is_superuser:
            return queryset

        if not user.gym:
            raise PermissionDenied("Usuario sin gimnasio asignado.")

        # 🔒 Filtrado por relación
        return queryset.filter(product__gym=user.gym)

    def perform_create(self, serializer):
        user = self.request.user
        product = serializer.validated_data.get("product")

        if not user.is_superuser and product.gym != user.gym:
            raise serializers.ValidationError(
                "No puedes gestionar inventario de otro gimnasio."
            )

        serializer.save()
