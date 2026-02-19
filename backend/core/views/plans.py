from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from core.models import Plan
from core.serializers import PlanSerializer
from .base import CompanyGymScopedViewSet


class PlanViewSet(CompanyGymScopedViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

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

        # STAFF
        else:
            serializer.save(gym=user.gym)



