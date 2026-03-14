from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Attendance
from core.serializers.client_attendance import ClientAttendanceSerializer
from datetime import datetime


class ClientMyAttendancesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "CLIENT" or not hasattr(user, "client_profile") or not user.client_profile:
            return Response({"detail": "Not authorized"}, status=403)

        client = user.client_profile

        queryset = (
            Attendance.objects
            .filter(client=client)
            .select_related("gym", "membership__plan")
            .order_by("-check_in_time")
        )

        month = request.query_params.get("month")

        if month:
            try:
                month_date = datetime.strptime(month, "%Y-%m").date()
                queryset = queryset.filter(
                    check_in_time__year=month_date.year,
                    check_in_time__month=month_date.month,
                )
            except ValueError:
                return Response(
                    {"detail": "Invalid month format. Use YYYY-MM"},
                    status=400
                )

        limit_param = request.query_params.get("limit", "100")

        try:
            limit = int(limit_param)
        except ValueError:
            return Response(
                {"detail": "Invalid limit. Use an integer value."},
                status=400
            )

        if limit <= 0:
            return Response(
                {"detail": "Invalid limit. Must be greater than 0."},
                status=400
            )

        limit = min(limit, 100)

        offset_param = request.query_params.get("offset", "0")

        try:
            offset = int(offset_param)
        except ValueError:
            return Response(
                {"detail": "Invalid offset. Use an integer value."},
                status=400
            )

        if offset < 0:
            return Response(
                {"detail": "Invalid offset. Must be 0 or greater."},
                status=400
            )

        all_rows = list(queryset[:500])

        grouped_time_rows = {}
        non_time_rows = []

        for attendance in all_rows:
            local_dt = timezone.localtime(attendance.check_in_time)
            local_day = local_dt.date()

            plan_type = None
            if attendance.membership and attendance.membership.plan:
                plan_type = attendance.membership.plan.plan_type

            if plan_type == "TIME":
                key = (attendance.client_id, local_day.isoformat())

                current = grouped_time_rows.get(key)
                if current is None:
                    grouped_time_rows[key] = attendance
                else:
                    current_dt = timezone.localtime(current.check_in_time)

                    # Nos quedamos con la asistencia más temprana del día
                    if local_dt < current_dt:
                        grouped_time_rows[key] = attendance
            else:
                non_time_rows.append(attendance)

        normalized_rows = list(grouped_time_rows.values()) + non_time_rows
        normalized_rows.sort(key=lambda x: x.check_in_time, reverse=True)

        now = timezone.localtime()
        month_start = now.date().replace(day=1)

        this_month_count = 0
        for attendance in normalized_rows:
            local_dt = timezone.localtime(attendance.check_in_time)
            if local_dt.date() >= month_start:
                this_month_count += 1

        last_attendance = normalized_rows[0] if normalized_rows else None

        summary = {
            "this_month_count": this_month_count,
            "total_count": len(normalized_rows),
            "last_visit_at": last_attendance.check_in_time if last_attendance else None,
        }

        paginated_rows = normalized_rows[offset:offset + limit]

        serializer = ClientAttendanceSerializer(
            paginated_rows,
            many=True,
            context={"request": request},
        )

        return Response({
            "meta": {
                "summary": summary,
                "count": len(normalized_rows),
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < len(normalized_rows),
                "has_previous": offset > 0,
            },
            "items": serializer.data
        })