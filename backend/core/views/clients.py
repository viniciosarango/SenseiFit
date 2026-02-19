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

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user

        # 🔒 Determinar gym de forma profesional y segura
        if user.is_superuser:
            gym_id = data.get("gym")
            if not gym_id:
                return Response(
                    {"detail": "Debe especificar el gym."},
                    status=400
                )
            try:
                gym = Gym.objects.get(id=gym_id)
            except Gym.DoesNotExist:
                return Response(
                    {"detail": "Gym inválido."},
                    status=400
                )
        else:
            if not user.gym:
                return Response(
                    {"detail": "El usuario no tiene un gimnasio asignado."},
                    status=400
                )
            gym = user.gym

        try:
            client, created_user, temp_password = create_client_with_user_service(
                gym=gym,
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                id_number=data.get("id_number"),
                phone=data.get("phone"),
                email=data.get("email"),
                birth_date=data.get("birth_date") or None,
                gender=data.get("gender") or None,
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

        except Exception as e:
            print(f"DEBUG ERROR en ClientViewSet: {str(e)}")
            return Response(
                {"detail": f"DEBUG: {str(e)}"},
                status=500
            )

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
