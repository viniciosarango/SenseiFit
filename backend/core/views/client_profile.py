from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from core.serializers.client_portal_serializer import ClientPortalSerializer


class ClientMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "CLIENT":
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        client = getattr(request.user, "client_profile", None)
        if not client:
            return Response({"detail": "Perfil no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientPortalSerializer(client, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        if request.user.role != "CLIENT":
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        client = getattr(request.user, "client_profile", None)
        if not client:
            return Response({"detail": "Perfil no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientPortalSerializer(
            client,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)