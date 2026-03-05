
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import get_random_string
from core.models.client import Client
from core.models.client_gym import ClientGym
from core.services.notification_service import send_client_credentials_email
from core.services.whatsapp_service import send_whatsapp_template
from core.models.contact_point import ContactPoint
from django.conf import settings
import random
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from core.services.integrations.make_webhook_service import send_make_event



User = get_user_model()


class ClientOnboardingError(Exception):
    pass

def upsert_contact_points_for_client(*, company, client, user=None, email=None, phone=None):
    """
    Crea/actualiza ContactPoints para el cliente.
    - Unicidad por (company, type, value)
    - Marca como primary el último email/teléfono enviado si existe
    - Por ahora: is_verified=False (luego implementamos verificación)
    """
    # EMAIL
    if email:
        value = str(email).strip().lower()
        cp, _ = ContactPoint.objects.get_or_create(
            company=company,
            type=ContactPoint.Types.EMAIL,
            value=value,
            defaults={"client": client, "user": user, "is_primary": True, "is_verified": False},
        )
        # Si existía, asegurar vínculo
        changed = False
        if cp.client_id != client.id:
            cp.client = client
            changed = True
        if user and cp.user_id != user.id:
            cp.user = user
            changed = True

        # ✅ Siempre: este email debe quedar como primary (y los demás EMAIL del cliente no)
        ContactPoint.objects.filter(
            company=company,
            client=client,
            type=ContactPoint.Types.EMAIL
        ).exclude(id=cp.id).update(is_primary=False)

        if not cp.is_primary:
            cp.is_primary = True
            changed = True

        if changed:
            cp.save()

    # PHONE
    if phone:
        value = str(phone).strip()
        cp, _ = ContactPoint.objects.get_or_create(
            company=company,
            type=ContactPoint.Types.PHONE,
            value=value,
            defaults={"client": client, "user": user, "is_primary": True, "is_verified": False},
        )
        changed = False
        if cp.client_id != client.id:
            cp.client = client
            changed = True
        if user and cp.user_id != user.id:
            cp.user = user
            changed = True

        # ✅ Siempre: este phone debe quedar como primary (y los demás PHONE del cliente no)
        ContactPoint.objects.filter(
            company=company,
            client=client,
            type=ContactPoint.Types.PHONE
        ).exclude(id=cp.id).update(is_primary=False)

        if not cp.is_primary:
            cp.is_primary = True
            changed = True

        if changed:
            cp.save()


@transaction.atomic
def create_client_with_user_service(
    *,
    company,
    gym,
    first_name,
    last_name,
    id_number=None,
    phone=None,
    email=None,
    birth_date=None,
    gender=None,
):

    print("✅ ONBOARDING SERVICE EJECUTADO", flush=True)
    if not company:
        raise ClientOnboardingError("La empresa es obligatoria.")

    if not gym:
        raise ClientOnboardingError("El gimnasio es obligatorio.")

    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    email = str(email).strip().lower() if email else None

    phone = str(phone).strip() if phone else None
    if phone:
        phone = phone.replace("+", "").replace(" ", "")
    
    id_number = str(id_number).strip() if id_number else None

    frontend_url = (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
    if frontend_url.startswith("http://") and "localhost" not in frontend_url:
        frontend_url = frontend_url.replace("http://", "https://", 1)
    
    login_url = f"{frontend_url}/auth/login" if frontend_url else None

    if not first_name:
        raise ClientOnboardingError("El nombre es obligatorio.")

    if not last_name:
        raise ClientOnboardingError("El apellido es obligatorio.")

    # 🔎 Buscar cliente existente (prioridad)
    client = None

    if id_number:
        client = Client.objects.filter(company=company, id_number=id_number).first()

    if not client and phone:
        client = Client.objects.filter(company=company, phone=phone).first()

    if not client and email:
        client = Client.objects.filter(company=company, email=email).first()

    # 🟢 Si cliente existe → actualizar datos
    if client:
        if phone:
            client.phone = phone
        if email:
            client.email = email
        if gender:
            client.gender = gender
        if birth_date:
            client.birth_date = birth_date

        client.save()

        upsert_contact_points_for_client(
            company=company,
            client=client,
            user=client.user,
            email=client.email,
            phone=client.phone
        )

        

        # ✅ WhatsApp (cliente existente con user) - único envío
        if client.user is not None and frontend_url and client.phone:
            user = client.user
            token = PasswordResetTokenGenerator().make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{frontend_url}/auth/reset-password?uid={uidb64}&token={token}"

            resp = send_whatsapp_template(
                to=(client.phone or "").replace("+", "").replace(" ", ""),
                template_name=getattr(settings, "WHATSAPP_TEMPLATE_CREDENTIALS", "sf_welcome_portal"),
                lang=getattr(settings, "WHATSAPP_TEMPLATE_LANG", "es_EC"),
                components=[
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": f"{client.first_name} {client.last_name}".strip() or "Hola"},
                            {"type": "text", "text": getattr(gym, "name", "") or "SenseiFit"},
                            {"type": "text", "text": reset_url},
                        ],
                    }
                ],
            )
            print("WA_SEND_EXISTING_USER:", resp, flush=True)



        # ✅ Si el cliente existe pero no tiene usuario, crearlo ahora (sin duplicar cliente)
        if client.user is None:
            temp_password = str(random.randint(100000, 999999))

            if email:
                username = email
            elif phone:
                username = phone
            else:
                base = f"{first_name}.{last_name}".lower().replace(" ", "")
                username = base or get_random_string(8)

            # evitar colisión
            if User.objects.filter(username=username).exists():
                base = username
                i = 1
                while User.objects.filter(username=f"{base}{i}").exists():
                    i += 1
                username = f"{base}{i}"

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=temp_password,
                role=User.Roles.CLIENT,
                company=company,
            )
            user.must_change_password = True
            user.save(update_fields=["must_change_password"])

            token = PasswordResetTokenGenerator().make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{frontend_url}/auth/reset-password?uid={uidb64}&token={token}"

            client.user = user
            client.save(update_fields=["user"])

            upsert_contact_points_for_client(
                company=company,
                client=client,
                user=user,
                email=client.email,
                phone=client.phone
            )

            if email:
                send_client_credentials_email(
                    email=user.email,
                    username=user.username,
                    temp_password=temp_password,
                    full_name=f"{first_name} {last_name}".strip(),
                    login_url=login_url,
                    reply_to=company.support_email
                )
            
    # 🔵 Si NO existe → crear cliente y user
    else:
        # ✅ PIN random de 6 dígitos
        temp_password = str(random.randint(100000, 999999))

        # ✅ username: email si existe, si no phone; si no, fallback a nombre.base
        if email:
            username = email
        elif phone:
            username = phone
        else:
            base = f"{first_name}.{last_name}".lower().replace(" ", "")
            username = base or get_random_string(8)
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{i}"
                i += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=temp_password,
            role=User.Roles.CLIENT,
            company=company,
        )

        # ✅ Obligatorio cambiar contraseña
        user.must_change_password = True
        user.save(update_fields=["must_change_password"])

        token = PasswordResetTokenGenerator().make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"{frontend_url}/auth/reset-password?uid={uidb64}&token={token}"

        client = Client.objects.create(
            company=company,
            first_name=first_name,
            last_name=last_name,
            id_number=id_number,
            phone=phone,
            email=email,
            birth_date=birth_date,
            gender=gender,
            user=user,
            
        )

        upsert_contact_points_for_client(
            company=company,
            client=client,
            user=user,
            email=email,
            phone=phone
        )

        # ✅ Email (si existe)
        if email:
            send_client_credentials_email(
                email=user.email,
                username=user.username,
                temp_password=temp_password,
                full_name=f"{first_name} {last_name}".strip(),
                login_url=login_url,
                reply_to=company.support_email
            )

        try:
            if client.phone:
                gym_name = getattr(gym, "name", "") or "SenseiFit"
                full_name = f"{first_name} {last_name}".strip() or "Hola"
                send_whatsapp_template(
                    to=client.phone,
                    template_name=getattr(settings, "WHATSAPP_TEMPLATE_CREDENTIALS", "sf_welcome_portal"),
                    lang=getattr(settings, "WHATSAPP_TEMPLATE_LANG", "es_EC"),
                    components=[
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": full_name},     # {{1}}
                                {"type": "text", "text": gym_name},      # {{2}}
                                {"type": "text", "text": reset_url}  # {{3}}
                            ],
                        }
                    ],
                )
        except Exception as e:
            print("WhatsApp error:", e)

    # 🔗 Crear relación con gym si no existe
    ClientGym.objects.get_or_create(
        client=client,
        gym=gym
    )

    # ✅ MAKE webhook: client.created (payload completo según tu modelo Client)
    try:
        # photo_url absoluto si hay request no lo tenemos aquí,
        # así que mandamos .url (relativo) y también un "photo_url" si FRONTEND_URL existe.
        photo_path = None
        try:
            if client.photo and getattr(client.photo, "url", None):
                photo_path = client.photo.url
        except Exception:
            photo_path = None

        # Normalizamos birth_date a string YYYY-MM-DD (o None)
        birth_date_str = str(client.birth_date) if client.birth_date else None

        send_make_event(
            event="client.created",
            data={
                "client": {
                    "id": client.id,
                    "first_name": client.first_name,
                    "last_name": client.last_name,
                    "full_name": client.full_name,

                    "country": client.country,
                    "document_type": client.document_type,
                    "id_number": client.id_number,

                    "hikvision_id": client.hikvision_id,

                    "email": client.email,
                    "phone": client.phone,

                    "birth_date": birth_date_str,
                    "gender": client.gender,  # ✅ AQUÍ VA EL GÉNERO (M/F/O)

                    "photo_path": photo_path,         # ej: /media/clients/xxx.jpg
                    "is_active": client.is_active,

                    "total_referrals": client.total_referrals,
                    "courtesy_pass_balance": client.courtesy_pass_balance,
                    "referred_by_id": client.referred_by_id,

                    "created_at": client.created_at.isoformat() if client.created_at else None,
                },

                "company": {
                    "id": company.id if company else None,
                    "name": getattr(company, "name", None),
                    "support_email": getattr(company, "support_email", None),
                },

                "gym": {
                    "id": getattr(gym, "id", None),
                    "name": getattr(gym, "name", None),
                },

                "user": {
                    "id": user.id if user else None,
                    "username": getattr(user, "username", None),
                    "email": getattr(user, "email", None),
                    "first_name": getattr(user, "first_name", None),
                    "last_name": getattr(user, "last_name", None),
                    "role": getattr(user, "role", None),
                    "must_change_password": getattr(user, "must_change_password", None),
                    "is_active": getattr(user, "is_active", None),
                    "date_joined": user.date_joined.isoformat() if getattr(user, "date_joined", None) else None,
                    "last_login": user.last_login.isoformat() if getattr(user, "last_login", None) else None,
                },

                # credenciales útiles para Kommo / Salesbot
                "temp_password": temp_password,

                "urls": {
                    "login_url": login_url,
                    "reset_url": reset_url,
                },
            },
        )
    except Exception as e:
        print("MAKE webhook error:", str(e), flush=True)

    return client, None, None