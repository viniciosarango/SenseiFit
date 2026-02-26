from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

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


    def partial_update(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        # STAFF: solo puede editar default_payment_grace_days con PIN y solo en su gym
        if user.role == user.Roles.STAFF:
            if not user.gym or instance.id != user.gym.id:
                return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

            pin = request.data.get("pin")
            if not pin or str(pin) != str(getattr(settings, "CANCEL_PIN", "")):
                return Response({"detail": "PIN incorrecto o faltante."}, status=status.HTTP_403_FORBIDDEN)

            # solo permitir este campo
            if set(request.data.keys()) - {"default_payment_grace_days", "pin"}:
                return Response({"detail": "Solo puede modificar el plazo de gracia."}, status=status.HTTP_400_BAD_REQUEST)

            return super().partial_update(request, *args, **kwargs)

        # ADMIN/SUPERUSER: normal (según tu CompanyGymScopedViewSet y permisos actuales)
        return super().partial_update(request, *args, **kwargs)
