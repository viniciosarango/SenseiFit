from rest_framework import viewsets
from core.models import GymClass
from core.serializers import GymClassSerializer



class GymClassViewSet(viewsets.ModelViewSet):
    queryset = GymClass.objects.all()
    serializer_class = GymClassSerializer