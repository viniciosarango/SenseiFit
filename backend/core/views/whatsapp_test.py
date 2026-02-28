from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from core.services.whatsapp_service import send_whatsapp_template


class WhatsAppTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        to = settings.WHATSAPP_TEST_TO
        data = send_whatsapp_template(
            to=to,
            template_name=settings.WHATSAPP_TEMPLATE_CREDENTIALS,
            lang=settings.WHATSAPP_TEMPLATE_LANG,
        )
        return Response({"ok": True, "meta": data}, status=status.HTTP_200_OK)