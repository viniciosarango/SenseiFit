from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from core.models import Client, Gym
from core.serializers import ClientSerializer
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

        if user.is_superuser:
            return Client.objects.filter(is_active=True)

        if user.role == user.Roles.ADMIN:
            return Client.objects.filter(
                company=user.company,
                is_active=True
            )

        if user.role == user.Roles.STAFF:
            return Client.objects.filter(
                is_active=True,
                gym_links__gym=user.gym
            ).distinct()

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

        client.is_active = False
        client.save()

        return Response({"detail": "Cliente desactivado correctamente."})

