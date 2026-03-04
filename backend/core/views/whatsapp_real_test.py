from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.services.whatsapp_service import send_whatsapp_template


class WhatsAppRealTemplateTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return Response({"detail": "No autorizado."}, status=403)
        
        to = request.data.get("to") or "593981891840"

        template_name = request.data.get("template_name") or "sf_welcome_portal"
        lang = request.data.get("lang") or "es_EC"  

        var1 = request.data.get("var1") or "Héctor"
        var2 = request.data.get("var2") or "Dorians Gym"
        var3 = request.data.get("var3") or "https://dorians.senseifit.app/auth/login"

        components = []

        # hello_world NO lleva parámetros
        if template_name != "hello_world":
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(var1)},
                        {"type": "text", "text": str(var2)},
                        {"type": "text", "text": str(var3)},
                    ],
                }
            ]

        result = send_whatsapp_template(
            to=to,
            template_name=template_name,
            lang=lang,
            components=components,
        )

        return Response(result)