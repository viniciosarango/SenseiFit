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
            gym_id = self.request.query_params.get("gym")

            if gym_id:
                try:
                    gym_id = int(gym_id)
                    return queryset.filter(gym_id=gym_id)
                except ValueError:
                    return queryset.none()

            return queryset

        # 🔒 ADMIN normal (no superuser)
        if user.role == user.Roles.ADMIN:
            if not user.company:
                return queryset.none()

            gym_id = self.request.query_params.get("gym")

            if gym_id:
                return queryset.filter(
                    gym_id=gym_id,
                    gym__company=user.company
                )

            return queryset.filter(gym__company=user.company)

        # 🔒 STAFF
        if user.role == user.Roles.STAFF:
            if not user.gym:
                return queryset.none()
            return queryset.filter(gym=user.gym)

        # 🔒 CLIENT
        if user.role == user.Roles.CLIENT:
            return queryset.none()

        return queryset.none()
