from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from core.models import Service
from core.serializers import ServiceSerializer
from .base import CompanyGymScopedViewSet


class ServiceViewSet(CompanyGymScopedViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        if not user.is_superuser and not user.gym:
            raise PermissionDenied("Usuario sin gimnasio asignado.")

        serializer.save(
            gym=user.gym if not user.is_superuser else serializer.validated_data.get("gym")
        )
