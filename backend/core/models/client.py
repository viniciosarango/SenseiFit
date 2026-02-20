from django.db import models
from django.db.models import Q
from .user import User
from .company import Company


class Client(models.Model):

    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    company = models.ForeignKey(
        Company,
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

    # País (ISO-2). Default EC para tu caso actual
    country = models.CharField(
        max_length=2,
        default="EC",
        help_text="Código ISO-2 del país (EC, CO, VE, etc.)",
        db_index=True
    )

    DOCUMENT_TYPE_CHOICES = [
        ("NATIONAL_ID", "Documento Nacional"),
        ("PASSPORT", "Pasaporte"),
    ]

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default="NATIONAL_ID",
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

    is_active = models.BooleanField(default=True, db_index=True)

    total_referrals = models.PositiveIntegerField(default=0)

    courtesy_pass_balance = models.PositiveIntegerField(default=0)

    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals_made"
    )

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
            models.Index(fields=["company", "country", "document_type", "id_number"]),
            models.Index(fields=["company", "is_active"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["company", "country", "document_type", "id_number"],
                name="unique_document_per_company",
                condition=Q(id_number__isnull=False)
            ),
        ]
        
        
