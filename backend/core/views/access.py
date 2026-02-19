# core/views/access.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import Membership, Client
from django.shortcuts import render

@api_view(["GET"])
def check_access(request):
    client_id = request.query_params.get("client_id")

    if not client_id:
        return Response(
            {"allowed": False, "reason": "NO_CLIENT_ID"},
            status=400
        )

    # 🔒 Determinar el gym desde el usuario autenticado
    user = request.user
    if not user.is_authenticated:
        return Response(
            {"allowed": False, "reason": "UNAUTHORIZED"},
            status=401
        )

    if not user.is_superuser and not user.gym:
        return Response(
            {"allowed": False, "reason": "NO_GYM_CONTEXT"},
            status=403
        )

    try:
        # 🔒 Filtrado multi-tenant
        if user.is_superuser:
            client = Client.objects.get(id=client_id)
        else:
            client = Client.objects.get(id=client_id, gym=user.gym)

    except Client.DoesNotExist:
        return Response(
            {"allowed": False, "reason": "CLIENT_NOT_FOUND"},
            status=404
        )

    membership = (
        Membership.objects
        .filter(client=client)
        .order_by("-start_date")
        .first()
    )

    if not membership:
        return Response(
            {"allowed": False, "reason": "NO_MEMBERSHIP"}
        )

    status = membership.operational_status

    if status == "ACTIVE":
        return Response({
            "allowed": True,
            "reason": "ACTIVE",
            "client": f"{client.first_name} {client.last_name}",
            "plan": membership.plan.name,
            "end_date": membership.end_date
        })

    return Response({
        "allowed": False,
        "reason": status
    })



def access_screen(request):
    return render(request, "access_screen.html")

