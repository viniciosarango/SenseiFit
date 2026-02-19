from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from core.models import User
from core.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # 🔒 Superuser SaaS → ve todo
        if user.is_superuser:
            return User.objects.all()

        # 🔒 ADMIN → todos los usuarios de su empresa
        if user.role == user.Roles.ADMIN:
            return User.objects.filter(company=user.company)

        # 🔒 STAFF → solo usuarios de su gym
        if user.role == user.Roles.STAFF:
            return User.objects.filter(gym=user.gym)

        # 🔒 CLIENT → solo a sí mismo
        return User.objects.filter(id=user.id)


    def perform_create(self, serializer):
        creator = self.request.user

        # 🔒 Solo ADMIN o superuser pueden crear usuarios
        if not creator.is_superuser and creator.role != creator.Roles.ADMIN:
            raise PermissionDenied("No tienes permisos para crear usuarios.")

        # 🔒 Evitar que alguien cree superusers
        if serializer.validated_data.get("is_superuser"):
            raise PermissionDenied("No puedes crear superusuarios.")

        # 🔒 Forzamos pertenencia a la empresa del creador
        serializer.save(
            company=creator.company,
            gym=serializer.validated_data.get("gym", creator.gym)
        )
