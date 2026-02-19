from django.db import models
from django.db.models import Q
from .gym import Gym
from .user import User


class Client(models.Model):

    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    # 🎯 Multi-tenant obligatorio: cada cliente pertenece a un Gym
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name='clients',
        db_index=True
    )

    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)

    id_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="N. de identificación",
        db_index=True
    )

    hikvision_id = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="ID del usuario en la lectora Hikvision (employeeNoString)",
        db_index=True
    )

    email = models.EmailField(null=True, blank=True)

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Nacimiento"
    )

    photo = models.ImageField(
        upload_to='clients/',
        null=True,
        blank=True
    )

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_profile'
    )

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name="Género"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ==============================
    # PROPIEDADES
    # ==============================

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.full_name}"

    # ==============================
    # CONSTRAINTS PROFESIONALES
    # ==============================

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["gym", "last_name"]),
            models.Index(fields=["gym", "id_number"]),
            models.Index(fields=["gym", "hikvision_id"]),
        ]
        constraints = [
            # 📌 Teléfono único por gimnasio
            models.UniqueConstraint(
                fields=['phone', 'gym'],
                name='unique_phone_per_gym',
                condition=Q(phone__isnull=False)
            ),

            # 📌 Cédula única por gimnasio
            models.UniqueConstraint(
                fields=['id_number', 'gym'],
                name='unique_id_number_per_gym',
                condition=Q(id_number__isnull=False)
            ),

            # 📌 Hikvision ID único por gimnasio
            models.UniqueConstraint(
                fields=['hikvision_id', 'gym'],
                name='unique_hikvision_per_gym',
                condition=Q(hikvision_id__isnull=False)
            ),
        ]
