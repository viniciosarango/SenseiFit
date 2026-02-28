from rest_framework import serializers
from core.models import User


class UserSerializer(serializers.ModelSerializer):
    # 🔹 Campos calculados y de solo lectura
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    gym_name = serializers.CharField(source='gym.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',

            'role',
            'role_display',

            'company',
            'company_name',

            'gym',
            'gym_name',

            'is_active',
            'is_staff',
            'is_superuser',
            'must_change_password',

            'last_login',
            'date_joined',

            'password',
        ]

        extra_kwargs = {
            'password': {'write_only': True},
            'is_staff': {'read_only': True},
            'is_superuser': {'read_only': True},
            'last_login': {'read_only': True},
            'date_joined': {'read_only': True},
        }

        read_only_fields = ['id']
