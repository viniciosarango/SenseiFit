from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.services.auth_resolver import resolve_user_by_identifier
from core.models import Company

class ResolveLoginIdentifierView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier", "")
        company = getattr(request, "company", None)
        if not company:
            company = Company.objects.first()   # ✅ fallback para local

        if not company:
            return Response({"ok": True, "username": None})

        user = resolve_user_by_identifier(company, identifier)
        return Response({"ok": True, "username": user.username if user else None})