from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from core.models import Plan
from core.serializers import PlanSerializer
from .base import CompanyGymScopedViewSet


class PlanViewSet(CompanyGymScopedViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        gym_id = self.request.query_params.get("gym")

        if gym_id and gym_id != "null":
            queryset = queryset.filter(gym_id=gym_id)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user


        # STAFF no puede crear planes
        if user.role == user.Roles.STAFF:
            raise PermissionDenied("No tienes permiso para crear planes.")

        # SUPERUSER
        if user.is_superuser:
            gym = serializer.validated_data.get("gym")
            if not gym:
                raise PermissionDenied("Debes especificar un gimnasio.")
            serializer.save(gym=gym)

        # ADMIN DE COMPANY
        elif user.role == user.Roles.ADMIN:
            gym = serializer.validated_data.get("gym")
            if not gym:
                raise PermissionDenied("Debes especificar un gimnasio.")
            if gym.company != user.company:
                raise PermissionDenied("No puedes crear planes para gimnasios de otra empresa.")
            serializer.save(gym=gym)


    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()

        # STAFF → forzar gym antes de validación
        if user.role == user.Roles.STAFF:
            data["gym"] = user.gym.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)
    

    def update(self, request, *args, **kwargs):
        if request.user.role == request.user.Roles.STAFF:
            raise PermissionDenied("No tienes permiso para editar planes.")
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        if request.user.role == request.user.Roles.STAFF:
            raise PermissionDenied("No tienes permiso para editar planes.")
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        # SUPERUSER → puede todo
        if user.is_superuser:
            instance.is_active = False
            instance.save()
            return Response({"detail": "Plan desactivado correctamente."})

        # ADMIN
        if user.role == user.Roles.ADMIN:
            if instance.gym.company != user.company:
                raise PermissionDenied("No puedes eliminar planes de otra empresa.")
            instance.is_active = False
            instance.save()
            return Response({"detail": "Plan desactivado correctamente."})

        # STAFF y CLIENT bloqueados
        raise PermissionDenied("No tienes permiso para eliminar planes.")



