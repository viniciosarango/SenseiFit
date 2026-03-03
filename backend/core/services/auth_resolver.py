from django.contrib.auth import get_user_model
from core.models.client import Client
from core.utils.phones import normalize_ec_phone

User = get_user_model()

def resolve_user_by_identifier(company, identifier: str):
    """
    identifier: email | username | phone | cedula
    company: limita búsqueda a tu empresa (clave para multi-tenant)
    """
    raw = (identifier or "").strip()
    if not raw:
        return None

    lower = raw.lower()

    # 1) email exact
    user = User.objects.filter(company=company, email__iexact=lower).first()
    if user:
        return user

    # 2) username exact (por si ya es email o phone guardado)
    user = User.objects.filter(company=company, username__iexact=lower).first()
    if user:
        return user

    # 3) teléfono normalizado
    phone_e164 = normalize_ec_phone(raw)
    if phone_e164:
        user = User.objects.filter(company=company, username=phone_e164).first()
        if user:
            return user

        # si tu DB guardó sin + (por compatibilidad)
        user = User.objects.filter(company=company, username=phone_e164.replace("+", "")).first()
        if user:
            return user

        # 4) si el teléfono está en Client (y user enlazado)
        client = Client.objects.filter(company=company, phone__in=[phone_e164, phone_e164.replace("+",""), raw]).select_related("user").first()
        if client and client.user:
            return client.user

    # 5) cédula (id_number)
    client = Client.objects.filter(company=company, id_number=raw).select_related("user").first()
    if client and client.user:
        return client.user

    return None