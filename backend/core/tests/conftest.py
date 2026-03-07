import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import (
    Company,
    Gym,
    Client,
    ClientGym,
    Plan,
    PaymentMethod,
    Membership,
)

User = get_user_model()


@pytest.fixture
def company_factory(db):
    def factory(**kwargs):
        data = {
            "name": kwargs.pop("name", "Dorians Gym"),
            "tax_id": kwargs.pop("tax_id", f"TAX-{timezone.now().timestamp()}"),
            "support_email": kwargs.pop("support_email", "test@example.com"),
        }
        data.update(kwargs)
        return Company.objects.create(**data)
    return factory


@pytest.fixture
def gym_factory(db, company_factory):
    counter = {"value": 0}

    def factory(**kwargs):
        counter["value"] += 1
        company = kwargs.pop("company", None) or company_factory()
        data = {
            "company": company,
            "name": kwargs.pop("name", f"Gym {counter['value']}"),
            "currency": kwargs.pop("currency", "USD"),
            "default_payment_grace_days": kwargs.pop("default_payment_grace_days", 7),
            "access_control_enabled": kwargs.pop("access_control_enabled", True),
            "auto_block_on_debt": kwargs.pop("auto_block_on_debt", True),
            "is_active": kwargs.pop("is_active", True),
        }
        data.update(kwargs)
        return Gym.objects.create(**data)
    return factory


@pytest.fixture
def user_factory(db, company_factory, gym_factory):
    counter = {"value": 0}

    def factory(**kwargs):
        counter["value"] += 1
        is_superuser = kwargs.pop("is_superuser", False)
        gym = kwargs.pop("gym", None)

        if is_superuser:
            company = kwargs.pop("company", None)
        else:
            gym = gym or gym_factory()
            company = kwargs.pop("company", None) or gym.company

        role = kwargs.pop("role", User.Roles.STAFF if not is_superuser else User.Roles.ADMIN)

        data = {
            "username": kwargs.pop("username", f"user{counter['value']}"),
            "first_name": kwargs.pop("first_name", "Test"),
            "last_name": kwargs.pop("last_name", f"User{counter['value']}"),
            "email": kwargs.pop("email", f"user{counter['value']}@example.com"),
            "role": role,
            "company": company,
            "gym": kwargs.pop("gym_override", gym),
            "is_superuser": is_superuser,
            "is_staff": kwargs.pop("is_staff", True),
        }
        data.update(kwargs)

        password = data.pop("password", "Test1234*")
        user = User.objects.create(**data)
        user.set_password(password)
        user.save()
        return user

    return factory


@pytest.fixture
def client_factory(db, company_factory, gym_factory):
    counter = {"value": 0}

    def factory(**kwargs):
        counter["value"] += 1
        gym = kwargs.pop("gym", None)
        company = kwargs.pop("company", None)

        if gym is None:
            if company is not None:
                gym = gym_factory(company=company)
            else:
                gym = gym_factory()

        company = company or gym.company

        data = {
            "company": company,
            "first_name": kwargs.pop("first_name", "Client"),
            "last_name": kwargs.pop("last_name", f"Test{counter['value']}"),
            "id_number": kwargs.pop("id_number", f"ID{counter['value']}"),
            "country": kwargs.pop("country", "EC"),
            "document_type": kwargs.pop("document_type", "NATIONAL_ID"),
            "email": kwargs.pop("email", f"client{counter['value']}@example.com"),
            "phone": kwargs.pop("phone", f"099000{counter['value']:04d}"),
            "is_active": kwargs.pop("is_active", True),
        }
        data.update(kwargs)

        client = Client.objects.create(**data)
        ClientGym.objects.get_or_create(client=client, gym=gym)
        return client

    return factory


@pytest.fixture
def plan_factory(db, gym_factory):
    counter = {"value": 0}

    def factory(**kwargs):
        counter["value"] += 1
        gym = kwargs.pop("gym", None) or gym_factory()
        plan_type = kwargs.pop("plan_type", "TIME")

        data = {
            "gym": gym,
            "name": kwargs.pop("name", f"Plan {counter['value']}"),
            "plan_type": plan_type,
            "price": kwargs.pop("price", Decimal("29.00")),
            "duration_days": kwargs.pop("duration_days", 30),
            "total_sessions": kwargs.pop("total_sessions", 20 if plan_type == "SESSIONS" else 0),
            "is_active": kwargs.pop("is_active", True),
        }
        data.update(kwargs)

        return Plan.objects.create(**data)

    return factory


@pytest.fixture
def payment_method_factory(db, gym_factory):
    counter = {"value": 0}

    def factory(**kwargs):
        counter["value"] += 1
        gym = kwargs.pop("gym", None) or gym_factory()
        data = {
            "gym": gym,
            "name": kwargs.pop("name", f"Efectivo {counter['value']}"),
            "active": kwargs.pop("active", True),
            "description": kwargs.pop("description", ""),
        }
        data.update(kwargs)
        return PaymentMethod.objects.create(**data)

    return factory


@pytest.fixture
def membership_factory(
    db,
    client_factory,
    gym_factory,
    plan_factory,
    user_factory,
):
    def factory(**kwargs):
        gym = kwargs.pop("gym", None) or gym_factory()
        client = kwargs.pop("client", None) or client_factory(gym=gym)
        plan = kwargs.pop("plan", None) or plan_factory(gym=gym)
        created_by = kwargs.pop("created_by", None) or user_factory(gym=gym)

        start_date = kwargs.pop("start_date", timezone.localdate())
        end_date = kwargs.pop("end_date", start_date + timezone.timedelta(days=plan.duration_days - 1))
        original_price = Decimal(str(kwargs.pop("original_price", plan.price)))
        discount_percent_applied = Decimal(str(kwargs.pop("discount_percent_applied", "0.00")))
        enrollment_fee_applied = Decimal(str(kwargs.pop("enrollment_fee_applied", "0.00")))
        paid_amount = Decimal(str(kwargs.pop("paid_amount", original_price)))
        sale_type = kwargs.pop("sale_type", None) 
        
        if sale_type is None:
            sale_type = "CASH" if paid_amount == original_price else "CREDIT"        
               
        payment_due_date = kwargs.pop("payment_due_date", None)

        membership = Membership.objects.create(
            client=client,
            gym=gym,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            payment_due_date=payment_due_date,
            action=kwargs.pop("action", "INSCRIPTION"),
            original_price=original_price,
            discount_percent_applied=discount_percent_applied,
            enrollment_fee_applied=enrollment_fee_applied,
            paid_amount=paid_amount,
            operational_status=kwargs.pop("operational_status", "ACTIVE"),
            created_by=created_by,
            notes=kwargs.pop("notes", ""),
            sale_type=sale_type,
            upgrade_credit=Decimal(str(kwargs.pop("upgrade_credit", "0.00"))),
            sessions_total=kwargs.pop("sessions_total", 0),
            sessions_consumed=kwargs.pop("sessions_consumed", 0),
            courtesy_qty=kwargs.pop("courtesy_qty", 0),
            courtesy_used=kwargs.pop("courtesy_used", 0),
            freeze_start_date=kwargs.pop("freeze_start_date", None),
            total_freeze_days=kwargs.pop("total_freeze_days", 0),
            freeze_requested_by=kwargs.pop("freeze_requested_by", None),
            unfreeze_requested_by=kwargs.pop("unfreeze_requested_by", None),
            freeze_timestamp=kwargs.pop("freeze_timestamp", None),
            unfreeze_timestamp=kwargs.pop("unfreeze_timestamp", None),
        )

        return membership

    return factory