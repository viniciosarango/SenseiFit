from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


User = get_user_model()


def normalize_phone(raw: str) -> str:
    """
    Normaliza teléfonos típicos de Ecuador:
    - '0981891840' -> '+593981891840'
    - '+593981891840' se queda igual
    - '593981891840' -> '+593981891840'
    """
    if not raw:
        return raw

    s = str(raw).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # ya viene internacional
    if s.startswith("+"):
        return s

    # viene como 593...
    if s.startswith("593"):
        return f"+{s}"

    # viene como 09xxxxxxxx (Ecuador)
    if s.startswith("09") and len(s) == 10 and s.isdigit():
        return f"+593{s[1:]}"  # quita el 0 inicial

    return s  # fallback


class FlexibleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Permite login con:
    - username (default)
    - email
    - phone (local 09.. o internacional)
    - id_number (cédula)
    """
    def validate(self, attrs):
        identifier = (attrs.get("username") or "").strip()
        password = attrs.get("password")

        # Intentar resolver usuario por varias llaves
        user = None

        # 1) username directo
        user = User.objects.filter(username__iexact=identifier).first()

        # 2) email
        if not user and "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()

        # 3) phone (normalizado)
        if not user:
            phone_norm = normalize_phone(identifier)
            # buscamos por username (si guardaste username=phone) o por email? no, por client.phone
            user = User.objects.filter(username=phone_norm).first()
            if not user:
                # si el username quedó como '098...' en algún caso viejo
                user = User.objects.filter(username=identifier).first()

            # buscar por Client.phone
            if not user:
                user = User.objects.filter(client_profile__phone=phone_norm).first() or User.objects.filter(client_profile__phone=identifier).first()

        # 4) cédula
        if not user and identifier.isdigit():
            user = User.objects.filter(client_profile__id_number=identifier).first()

        if not user:
            raise self.authentication_failed("No se encontró usuario con esos datos.")

        # Validar password
        if not user.check_password(password):
            raise self.authentication_failed("Usuario o contraseña incorrectos.")

        # SimpleJWT espera el "username" real en attrs
        attrs["username"] = user.username
        return super().validate(attrs)


class FlexibleTokenObtainPairView(TokenObtainPairView):
    serializer_class = FlexibleTokenObtainPairSerializer