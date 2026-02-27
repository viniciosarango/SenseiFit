from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status

from core.services.clients import deactivate_client_service, reactivate_client_service


from core.models import Client, Gym
from core.serializers import ClientSerializer
from core.serializers.client_profile import ClientProfileSerializer
from core.services.client_onboarding_service import (
    create_client_with_user_service,
    ClientOnboardingError
)
from core.serializers.client_portal_serializer import ClientPortalSerializer
from .base import CompanyGymScopedViewSet


class ClientViewSet(CompanyGymScopedViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        status = self.request.query_params.get("status", "active")  # active|inactive|all

        def apply_status(qs):
            if status == "inactive":
                return qs.filter(is_active=False)
            if status == "all":
                return qs
            return qs.filter(is_active=True)

        if user.is_superuser:
            return apply_status(Client.objects.all())

        if user.role == user.Roles.ADMIN:
            return apply_status(Client.objects.filter(company=user.company))

        if user.role == user.Roles.STAFF:
            return apply_status(
                Client.objects.filter(gym_links__gym=user.gym).distinct()
            )

        return Client.objects.none()

    
    
    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        
        if not (user.is_superuser or user.role in [user.Roles.ADMIN, user.Roles.STAFF]):
            return Response({"detail": "No tienes permiso para crear clientes."}, status=403)

        # 🔥 Determinar empresa y gym según rol
        if user.is_superuser:
            company_id = data.get("company")
            gym_id = data.get("gym")

            if not company_id:
                return Response({"detail": "Debe especificar la empresa."}, status=400)

            if not gym_id:
                return Response({"detail": "Debe especificar el gimnasio."}, status=400)

            from core.models import Company, Gym

            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return Response({"detail": "Empresa inválida."}, status=400)

            try:
                gym = Gym.objects.get(id=gym_id, company=company)
            except Gym.DoesNotExist:
                return Response({"detail": "Gimnasio inválido para esta empresa."}, status=400)

        elif user.role == user.Roles.ADMIN:
            company = user.company

            gym_id = data.get("gym")
            if not gym_id:
                return Response({"detail": "Debe especificar el gimnasio."}, status=400)

            from core.models import Gym
            try:
                gym = Gym.objects.get(id=gym_id, company=company)
            except Gym.DoesNotExist:
                return Response({"detail": "Gimnasio inválido."}, status=400)

        elif user.role == user.Roles.STAFF:
            company = user.company
            gym = user.gym

        else:
            return Response({"detail": "No tienes permiso para crear clientes."}, status=403)

        # 🔥 Crear cliente
        try:

            # 🔥 Validar primero con serializer
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # 🔥 Luego crear cliente
            client, _, _ = create_client_with_user_service(
                company=company,
                gym=gym,
                first_name=serializer.validated_data.get("first_name"),
                last_name=serializer.validated_data.get("last_name"),
                id_number=serializer.validated_data.get("id_number"),
                phone=serializer.validated_data.get("phone"),
                email=serializer.validated_data.get("email"),
                birth_date=serializer.validated_data.get("birth_date"),
                gender=serializer.validated_data.get("gender"),
            )

            if data.get("hikvision_id"):
                client.hikvision_id = data.get("hikvision_id")

            if 'photo' in request.FILES:
                client.photo = request.FILES['photo']

            client.save()
            serializer = self.get_serializer(client)
            return Response(serializer.data, status=201)

        except ClientOnboardingError as e:
            return Response({"detail": str(e)}, status=400)
        

    def update(self, request, *args, **kwargs):
        user = request.user
        client = self.get_object()

        # 🔒 Superuser puede todo
        if user.is_superuser:
            return super().update(request, *args, **kwargs)

        # 🔒 Admin solo clientes de su company
        if user.role == user.Roles.ADMIN:
            if client.company_id != user.company_id:
                return Response({"detail": "No autorizado."}, status=403)
            return super().update(request, *args, **kwargs)

        # 🔒 Staff solo clientes de su gym
        if user.role == user.Roles.STAFF:
            if not client.gym_links.filter(gym=user.gym).exists():
                return Response({"detail": "No autorizado."}, status=403)
            return super().update(request, *args, **kwargs)

        return Response({"detail": "No autorizado."}, status=403)



    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        if user.role != 'CLIENT':
            return Response({"detail": "No autorizado."}, status=403)

        try:
            client = user.client_profile
        except:
            return Response({"detail": "Cliente no encontrado."}, status=404)

        if request.method == 'PATCH':
            serializer = ClientPortalSerializer(
                client,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = ClientPortalSerializer(client)
        return Response(serializer.data)
    


    def destroy(self, request, *args, **kwargs):
        user = request.user
        client = self.get_object()

        # Permisos
        if not (
            user.is_superuser or
            (user.role == user.Roles.ADMIN and client.company_id == user.company_id) or
            (user.role == user.Roles.STAFF and client.gym_links.filter(gym=user.gym).exists())
        ):
            return Response({"detail": "No autorizado."}, status=403)
        
        deactivate_client_service(client=client, requested_by=request.user)
        return Response({"detail": "Cliente desactivado correctamente."})
    


    @action(detail=True, methods=["post"], url_path="reactivate")
    def reactivate(self, request, pk=None):
        user = request.user

        try:
            client = Client.objects.get(pk=pk)  # incluye inactivos
        except Client.DoesNotExist:
            return Response({"detail": "Cliente no encontrado."}, status=404)

        # permisos iguales a destroy
        if not (
            user.is_superuser or
            (user.role == user.Roles.ADMIN and client.company_id == user.company_id) or
            (user.role == user.Roles.STAFF and client.gym_links.filter(gym=user.gym).exists())
        ):
            return Response({"detail": "No autorizado."}, status=403)
        
        if client.is_active:
            return Response({"detail": "Cliente ya está activo."}, status=status.HTTP_200_OK)

        reactivate_client_service(client=client, requested_by=user)
        return Response({"detail": "Cliente reactivado correctamente."}, status=status.HTTP_200_OK)
    


    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        user = request.user

        try:
            client = Client.objects.get(pk=pk)  # incluye inactivos
        except Client.DoesNotExist:
            return Response({"detail": "Cliente no encontrado."}, status=404)

        # permisos (mismos que destroy)
        if not (
            user.is_superuser or
            (user.role == user.Roles.ADMIN and client.company_id == user.company_id) or
            (user.role == user.Roles.STAFF and client.gym_links.filter(gym=user.gym).exists())
        ):
            return Response({"detail": "No autorizado."}, status=403)

        if not client.is_active:
            return Response({"detail": "Cliente ya está inactivo."}, status=status.HTTP_200_OK)
        
        # PIN solo para STAFF
        if user.role == user.Roles.STAFF:
            from django.conf import settings
            pin = request.data.get("pin")
            if not pin:
                return Response({"detail": "PIN requerido."}, status=403)
            if str(pin) != str(getattr(settings, "CANCEL_PIN", "")):
                return Response({"detail": "PIN incorrecto."}, status=403)

        from core.services.clients import deactivate_client_service
        deactivate_client_service(client=client, requested_by=user)

        return Response({"detail": "Cliente desactivado correctamente."}, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=["get"], url_path="profile")
    def profile(self, request, pk=None):
        # Usa el MISMO objeto que retrieve (respeta permisos + filtros)
        client = self.get_object()

        serializer = ClientProfileSerializer(client, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

