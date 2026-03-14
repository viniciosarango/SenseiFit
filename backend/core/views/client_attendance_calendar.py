from datetime import datetime,date
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Attendance


class ClientAttendanceCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "CLIENT" or not hasattr(user, "client_profile") or not user.client_profile:
            return Response({"detail": "Not authorized"}, status=403)

        month = request.query_params.get("month")
        if not month:
            return Response({"detail": "month is required. Use YYYY-MM"}, status=400)

        try:
            month_date = datetime.strptime(month, "%Y-%m").date()
            year = month_date.year
            month_number = month_date.month

            first_day_of_month = date(year, month_number, 1)

            if month_number == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month_number + 1, 1)

            days_in_month = (next_month - first_day_of_month).days
            today_local = timezone.localdate()
            is_current_month = (today_local.year == year and today_local.month == month_number)
        
        except ValueError:
            return Response({"detail": "Invalid month format. Use YYYY-MM"}, status=400)

        client = user.client_profile

        queryset = (
            Attendance.objects
            .filter(
                client=client,
                check_in_time__year=month_date.year,
                check_in_time__month=month_date.month,
            )
            .select_related("membership__plan")
            .order_by("-check_in_time")
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
                    if local_dt < current_dt:
                        grouped_time_rows[key] = attendance
            else:
                non_time_rows.append(attendance)

        normalized_rows = list(grouped_time_rows.values()) + non_time_rows

        attendance_days = sorted({
            timezone.localtime(att.check_in_time).date().isoformat()
            for att in normalized_rows
        })

        attendance_map = {
            day: {
                "attended": True
            }
            for day in attendance_days
        }

        return Response({
            "meta": {
                "month": month,
                "year": year,
                "month_number": month_number,
                "days_in_month": days_in_month,
                "total_attendances": len(normalized_rows),
                "attendance_days_count": len(attendance_days),
                "is_current_month": is_current_month,
                "today": today_local.isoformat(),
            },
            "items": attendance_days,
            "map": attendance_map,
        })        