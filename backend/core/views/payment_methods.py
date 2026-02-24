from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from core.models import PaymentMethod
from core.serializers import PaymentMethodSerializer
from .base import CompanyGymScopedViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status



class PaymentMethodViewSet(CompanyGymScopedViewSet):
    # 1. Define el queryset base aquí
    queryset = PaymentMethod.objects.all() 
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        user = self.request.user

        # 🔥 SUPERUSER → libre
        if user.is_superuser:
            serializer.save()
            return

        # 🔒 ADMIN → puede crear para gyms de su company
        if user.role == user.Roles.ADMIN:
            gym = serializer.validated_data.get("gym")

            if not gym:
                raise PermissionDenied("Debe seleccionar un gimnasio.")

            if gym.company != user.company:
                raise PermissionDenied("No puede crear métodos fuera de su empresa.")

            serializer.save()
            return

        # ❌ STAFF → NO puede crear
        raise PermissionDenied("No tienes permisos para crear métodos de pago.")
    


    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        user = request.user
        payment_method = self.get_object()

        # 🔥 SUPERUSER → permitido
        if user.is_superuser:
            pass

        # 🔒 ADMIN → solo dentro de su company
        elif user.role == user.Roles.ADMIN:
            if payment_method.gym.company != user.company:
                return Response(
                    {"detail": "No autorizado."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # ❌ STAFF → bloqueado
        else:
            return Response(
                {"detail": "No tienes permisos para modificar métodos de pago."},
                status=status.HTTP_403_FORBIDDEN
            )

        payment_method.active = not payment_method.active
        payment_method.save(update_fields=["active"])

        return Response(
            {
                "detail": "Estado actualizado correctamente.",
                "active": payment_method.active
            },
            status=status.HTTP_200_OK
        )