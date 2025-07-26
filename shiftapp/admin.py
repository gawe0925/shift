from datetime import datetime
from django.contrib import admin
from .models import Members, Shift, StaffShift


@admin.register(Members)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "last_name",
        "first_name",
        "email",
        "mobile",
        "permanent_position",
        "position_type",
        "part_time_rate",
        "is_staff",
    )

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = (
        "shift_name",
        "start_time",
        "end_time",
        "get_break_min_display",
        "daily_work_hours_display",
    )

    def daily_work_hours_display(self, obj):
        return f"{obj.daily_work_hours():.2f} hours"
    daily_work_hours_display.short_description = "Daily Work Hours"


@admin.register(StaffShift)
class StaffShiftAdmin(admin.ModelAdmin):
    list_display = (
        "shift_date",
        "days",
        "staff",
        "staff_position",
        "shift",
        "cover_shift",
        "alternative_staff",
    )

    def staff_position(self, obj):
        return obj.staff_position()
    staff_position.short_description = "Position"

    def days(self, obj):
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_index = obj.shift_date.weekday()
        return weekdays[weekday_index]
    days.short_description = "Days"
        