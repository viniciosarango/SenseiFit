from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from core.models import Gym
from core.serializers import GymSerializer


class GymViewSet(viewsets.ModelViewSet):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Superuser SaaS
        if user.is_superuser:
            return self.queryset

        # Debe tener empresa
        if not user.company:
            raise PermissionDenied("Usuario sin empresa asignada.")

        # Solo gimnasios de su empresa
        return self.queryset.filter(company=user.company)

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise PermissionDenied("Usuario sin empresa asignada.")

        serializer.save(company=user.company)
