from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q

from .company import Company
from .gym import Gym


class User(AbstractUser):

    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        STAFF = 'STAFF', 'Staff'
        CLIENT = 'CLIENT', 'Cliente'

    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.CLIENT
    )

    phone = models.CharField(max_length=20, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users"
    )

    gym = models.ForeignKey(
        Gym,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members'
    )

    # ------------------------------------------------------------------
    # VALIDACIÓN ESTRUCTURAL (SaaS Profesional)
    # ------------------------------------------------------------------
    def clean(self):
        super().clean()

        # Superuser SaaS → libre
        if self.is_superuser:
            return

        # Todo usuario normal debe tener company
        if not self.company:
            raise ValidationError("Todo usuario debe pertenecer a una empresa.")

        # Si tiene gym → ese gym debe pertenecer a su company
        if self.gym and self.gym.company != self.company:
            raise ValidationError(
                "El gimnasio no pertenece a la empresa del usuario."
            )

        # CLIENT siempre debe tener gym
        if self.role == self.Roles.CLIENT and not self.gym:
            raise ValidationError(
                "Un cliente debe estar asignado a un gimnasio."
            )

        # STAFF debe tener gym
        if self.role == self.Roles.STAFF and not self.gym:
            raise ValidationError(
                "El staff debe estar asignado a un gimnasio."
            )

        # ADMIN puede no tener gym (admin global de company)
    
    # ------------------------------------------------------------------
    # UTILIDADES PROFESIONALES
    # ------------------------------------------------------------------
    @property
    def is_company_admin(self):
        return self.role == self.Roles.ADMIN

    @property
    def is_staff_member(self):
        return self.role == self.Roles.STAFF

    @property
    def is_client(self):
        return self.role == self.Roles.CLIENT

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    class Meta:
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["gym"]),
            models.Index(fields=["role"]),
        ]
