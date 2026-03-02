
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

    if not company:
        raise ClientOnboardingError("La empresa es obligatoria.")

    if not gym:
        raise ClientOnboardingError("El gimnasio es obligatorio.")

    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    email = str(email).strip().lower() if email else None
    phone = str(phone).strip() if phone else None
    id_number = str(id_number).strip() if id_number else None
    frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")
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

            # ✅ WhatsApp Welcome (si hay teléfono)
            try:
                if client.phone:
                    gym_name = getattr(gym, "name", "") or "SenseiFit"
                    full_name = f"{first_name} {last_name}".strip() or "Hola"
                    send_whatsapp_template(
                        to=client.phone,
                        template_name="sf_welcome_portal",
                        lang="es_EC",
                        components=[
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": full_name},     # {{1}}
                                    {"type": "text", "text": gym_name},      # {{2}}
                                    {"type": "text", "text": login_url or ""}# {{3}}
                                ],
                            }
                        ],
                    )
            except Exception as e:
                print("WhatsApp error:", e)

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
                    template_name="sf_welcome_portal",
                    lang="es_EC",
                    components=[
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": full_name},     # {{1}}
                                {"type": "text", "text": gym_name},      # {{2}}
                                {"type": "text", "text": login_url or ""}# {{3}}
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

    return client, None, None