from django.utils import timezone
from rest_framework import serializers
from core.models import Attendance


class ClientAttendanceSerializer(serializers.ModelSerializer):

    gym_name = serializers.CharField(source="gym.name", read_only=True)
    gym_id = serializers.IntegerField(source="gym.id", read_only=True)
    plan_name = serializers.SerializerMethodField()
    plan_id = serializers.SerializerMethodField()
    device_label = serializers.SerializerMethodField()    

    method_label = serializers.SerializerMethodField()
    access_status_label = serializers.SerializerMethodField()

    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            "id",
            "check_in_time",
            "date",
            "time",
            "access_status",
            "access_status_label",
            "is_allowed",
            "message_displayed",
            "method",
            "method_label",
            "gym_id",
            "gym_name",
            "plan_id",
            "plan_name",
            "device_id",
            "device_label",
        ]

    def get_plan_name(self, obj):
        if obj.membership and obj.membership.plan:
            return obj.membership.plan.name
        return None

    def get_plan_id(self, obj):
        if obj.membership and obj.membership.plan:
            return obj.membership.plan.id
        return None

    def get_method_label(self, obj):
        return obj.get_method_display()

    def get_access_status_label(self, obj):
        return obj.get_access_status_display()

    def get_date(self, obj):
        if not obj.check_in_time:
            return None
        return timezone.localtime(obj.check_in_time).date()

    def get_time(self, obj):
        if not obj.check_in_time:
            return None
        return timezone.localtime(obj.check_in_time).strftime("%H:%M")
    
    def get_device_label(self, obj):
        return obj.device_id or "Dispositivo no identificado"