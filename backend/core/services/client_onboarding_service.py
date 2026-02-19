# core/services/client_onboarding_service.py

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import get_random_string
from core.models.client import Client

from core.services.notification_service import send_client_credentials_email


User = get_user_model()


class ClientOnboardingError(Exception):
    pass


@transaction.atomic
def create_client_with_user_service(
    *,
    gym,
    first_name,
    last_name,
    id_number=None,
    phone=None,
    email=None,
    birth_date=None,
    gender=None,
):
    if not gym:
        raise ClientOnboardingError("El gimnasio es obligatorio.")

    # 🔒 NUEVO — Blindaje de nombres (evita NULL en AbstractUser)
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()

    if not first_name:
        raise ClientOnboardingError("El nombre es obligatorio.")

    if not last_name:
        raise ClientOnboardingError("El apellido es obligatorio.")

    # 🔒 Normalización fuerte del email
    email = (email or "").strip().lower()

    if not email:
        email = None

    if email and User.objects.filter(email=email).exists():
        raise ClientOnboardingError(
            "Ya existe un usuario registrado con este email."
        )


    if id_number:
        if Client.objects.filter(
            id_number=id_number,
            gym=gym
        ).exists():
            raise ClientOnboardingError(
                "Esta cédula ya está registrada en esta sucursal."
            )

    # 🔒 Normalización fuerte del teléfono
    phone = (phone or "").strip()

    if not phone:
        phone = None

    if phone and Client.objects.filter(
        phone=phone,
        gym=gym
    ).exists():
        raise ClientOnboardingError(
            "Este número ya está registrado en esta sucursal."
        )


    # Password temporal
    temp_password = get_random_string(length=10)

    # Username
    if email:
        username = email
    else:
        base = f"{first_name}.{last_name}".lower().replace(" ", "")
        username = base or get_random_string(8)
        i = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{i}"
            i += 1

    # Crear User
    print("ANTES DE CREAR USER, email =", repr(email))
    user = User.objects.create_user(
        username=username,
        email=email,  
        first_name=first_name,  # 🔒 ya nunca será None
        last_name=last_name,    # 🔒 ya nunca será None
        password=temp_password,
        role=User.Roles.CLIENT,
        gym=gym,
        company=gym.company,
    )
    # 🔍 DEBUG
    print("DESPUÉS DE CREAR USER, email guardado =", repr(user.email))

    # Crear Client
    client = Client.objects.create(
        gym=gym,
        first_name=first_name,
        last_name=last_name,
        id_number=id_number or None,
        phone=phone,
        email=email,
        birth_date=birth_date or None,
        gender=gender or None,
        user=user,
    )

    # Enviar credenciales solo si hay email
    if email:
        send_client_credentials_email(
            email=user.email,
            username=user.username,
            temp_password=temp_password
        )

    return client, user, temp_password


