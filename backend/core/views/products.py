from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from core.models import Product
from core.serializers import ProductSerializer
from .base import CompanyGymScopedViewSet


class ProductViewSet(CompanyGymScopedViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('name')

    def perform_create(self, serializer):
        user = self.request.user

        if not user.is_superuser and not user.gym:
            raise PermissionDenied("Usuario sin gimnasio asignado.")

        serializer.save(
            gym=user.gym if not user.is_superuser else serializer.validated_data.get("gym")
        )
