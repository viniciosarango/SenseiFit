from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from core.models import Company
from core.serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # SUPERUSER → todas
        if user.is_superuser:
            return Company.objects.all()

        # ADMIN → solo su company
        if user.role == user.Roles.ADMIN:
            if not user.company:
                raise PermissionDenied("Administrador sin empresa asignada.")
            return Company.objects.filter(id=user.company_id)

        # STAFF → no puede listar empresas
        raise PermissionDenied("No tienes permiso para ver empresas.")

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(
                {"detail": "Solo superusuarios pueden crear empresas."},
                status=403
            )
        return super().create(request, *args, **kwargs)