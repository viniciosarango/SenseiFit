from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import get_random_string
from core.models.client import Client
from core.models.client_gym import ClientGym
from core.services.notification_service import send_client_credentials_email

User = get_user_model()


class ClientOnboardingError(Exception):
    pass


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

    # 🔵 Si NO existe → crear cliente y user
    else:
        temp_password = get_random_string(length=10)

        if email:
            username = email
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

        if email:
            send_client_credentials_email(
                email=user.email,
                username=user.username,
                temp_password=temp_password
            )

    # 🔗 Crear relación con gym si no existe
    ClientGym.objects.get_or_create(
        client=client,
        gym=gym
    )

    return client, None, None