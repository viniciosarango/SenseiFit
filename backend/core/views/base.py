from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied


class CompanyGymScopedViewSet(viewsets.ModelViewSet):
    

    def get_queryset(self):
        if not hasattr(self, "queryset") or self.queryset is None:
            raise AttributeError(
                f"{self.__class__.__name__} debe definir un queryset."
            )

        user = self.request.user
        queryset = self.queryset

        if user.is_superuser:
            return queryset

        if not user.gym and not user.company:
            raise PermissionDenied("Usuario sin contexto de empresa.")

        # ADMIN → todos los gyms de su company
        if user.role == user.Roles.ADMIN:
            return queryset.filter(gym__company=user.company)

        # STAFF → solo su gym
        if user.role == user.Roles.STAFF:
            return queryset.filter(gym=user.gym)

        # CLIENT → solo sus propias memberships
        if user.role == user.Roles.CLIENT:
            return queryset.filter(client__user=user)

        return queryset.none()
