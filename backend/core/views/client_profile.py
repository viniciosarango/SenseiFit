from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Client
from core.serializers.client_portal_serializer import ClientPortalSerializer



class ClientMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'CLIENT':
            return Response({"detail": "No autorizado."}, status=403)

        try:
            client = request.user.client_profile
        except Client.DoesNotExist:
            return Response({"detail": "Perfil no encontrado."}, status=404)

        serializer = ClientPortalSerializer(client)
        return Response(serializer.data)

    def patch(self, request):
        if request.user.role != 'CLIENT':
            return Response({"detail": "No autorizado."}, status=403)

        client = request.user.client_profile

        serializer = ClientPortalSerializer(
            client,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

