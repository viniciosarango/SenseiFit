import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
def whatsapp_webhook(request):
    # Verificación del webhook (Meta)
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == getattr(settings, "WHATSAPP_VERIFY_TOKEN", ""):
            return HttpResponse(challenge, status=200)

        return HttpResponse("Verification failed", status=403)

    # Recepción de eventos (statuses, messages)
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            payload = {"raw": request.body.decode("utf-8", errors="ignore")}

        print("WA_WEBHOOK_PAYLOAD=", payload, flush=True)
        return JsonResponse({"ok": True})

    return HttpResponse(status=405)