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
        queryset = self.queryset

        # 🔥 SUPERUSER SaaS
        if user.is_superuser:
            company_id = self.request.query_params.get("company")

            # Si viene filtro por company → aplicarlo
            if company_id:
                return queryset.filter(company_id=company_id)

            return queryset

        # 🔒 Debe tener empresa
        if not user.company:
            raise PermissionDenied("Usuario sin empresa asignada.")

        # 🔒 ADMIN y STAFF → solo su empresa
        return queryset.filter(company=user.company)

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise PermissionDenied("Usuario sin empresa asignada.")

        serializer.save(company=user.company)
