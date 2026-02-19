from django.db import models


class CompanyGymQuerySet(models.QuerySet):
    """
    QuerySet multi-tenant profesional.
    Centraliza el aislamiento por company / gym.
    """

    def for_user(self, user):
        if not user or not user.is_authenticated:
            return self.none()

        # 🔵 Superuser → visión total
        if user.is_superuser:
            return self

        # 🔴 Usuario sin contexto
        if not user.gym and not user.company:
            return self.none()

        # 🟢 ADMIN → todos los gyms de su company
        if user.role == user.Roles.ADMIN:
            return self.filter(gym__company=user.company)

        # 🟡 STAFF / CLIENT → solo su gym
        return self.filter(gym=user.gym)


class CompanyGymManager(models.Manager):
    """
    Manager que obliga a usar el QuerySet seguro.
    """

    def get_queryset(self):
        return CompanyGymQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)
