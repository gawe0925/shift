from datetime import date, timedelta
from collections import defaultdict
import random
from .models import *

import calendar
from datetime import date
from collections import defaultdict

def generate_monthly_weeks(year: int, month: int):
    """
    依據指定年份與月份，產生每週的平日、週六、週日列表，
    並合併平日不足三天的週至前一週或下一週。
    回傳資料結構為：
    [
        {
            "weekdays": [...],
            "saturdays": [...],
            "sundays": [...]
        },
        ...
    ]
    """
    cal = calendar.Calendar()
    raw_weeks = defaultdict(lambda: {"weekdays": [], "saturdays": [], "sundays": []})

    # 將每一天歸入對應的週
    for day, weekday in cal.itermonthdays2(year, month):
        if day == 0:
            continue  # 非本月日
        d = date(year, month, day)
        week_num = d.isocalendar()[1]
        if weekday == 5:
            raw_weeks[week_num]["saturdays"].append(d.isoformat())
        elif weekday == 6:
            raw_weeks[week_num]["sundays"].append(d.isoformat())
        else:
            raw_weeks[week_num]["weekdays"].append(d.isoformat())

    # 按週排序並轉為 list
    sorted_weeks = [raw_weeks[w] for w in sorted(raw_weeks.keys())]

    # 合併平日不足三天的週
    cleaned_weeks = []
    buffer = None

    for week in sorted_weeks:
        if len(week["weekdays"]) < 3:
            if cleaned_weeks:
                # 合併到上一週
                prev = cleaned_weeks.pop()
                combined = {
                    "weekdays": sorted(prev["weekdays"] + week["weekdays"]),
                    "saturdays": sorted(prev["saturdays"] + week["saturdays"]),
                    "sundays": sorted(prev["sundays"] + week["sundays"]),
                }
                cleaned_weeks.append(combined)
            else:
                # 沒上一週可合併，就暫存，等下週再合併
                buffer = week
        else:
            if buffer:
                # 合併上一次的不足週
                combined = {
                    "weekdays": sorted(buffer["weekdays"] + week["weekdays"]),
                    "saturdays": sorted(buffer["saturdays"] + week["saturdays"]),
                    "sundays": sorted(buffer["sundays"] + week["sundays"]),
                }
                cleaned_weeks.append(combined)
                buffer = None
            else:
                cleaned_weeks.append(week)

    return cleaned_weeks

def casual_weekly_schedule(week_list, casual_list):
    after = Shift.objects.filter(shift_name='Afternoon Shift').first()
    # weekend shifts
    weekend_morning = Shift.objects.filter(shift_name='Weekend Morning').first()
    weekend_mid = Shift.objects.filter(shift_name='Weekend Midday').first()
    # saturdays only
    helper_a = list(Shift.objects.filter(shift_name='Weekend Helper A'))
    helper_b = list(Shift.objects.filter(shift_name='Weekend Helper B'))
    staffshifts = []

    for _, week in enumerate(week_list, start=1):
        schedule = defaultdict(list)
        person_shift_counts = {staff: 0 for staff in casual_list}

        for day in week.get("weekdays", []):
            available = [staff for staff in casual_list if person_shift_counts[staff] < 4]
            if not available:
                continue
            staff = random.choice(available)
            staffshifts.append(StaffShift(shift_date=day, staff=staff, shift=after))
            person_shift_counts[staff] += 1

        for day in week.get("saturdays", []):
            available = [staff for staff in casual_list if person_shift_counts[staff] < 4 and day not in schedule[staff]]
            random.shuffle(available)
            sequence_number = 0
            helper = random.choice(helper_a + helper_b)
            shift_mape = {1: weekend_morning, 2: weekend_mid, 3: helper}
            for staff in available[:3]:
                sequence_number += 1
                staffshifts.append(StaffShift(shift_date=day, staff=staff, shift=shift_mape[sequence_number]))
                if sequence_number == 3:
                    sequence_number = 0
                person_shift_counts[staff] += 1

        for day in week.get("sundays", []):
            available = [staff for staff in casual_list if person_shift_counts[staff] < 4 and day not in schedule[staff]]
            random.shuffle(available)
            sequence_number = 0
            shift_mape = {1: weekend_morning, 2: weekend_mid}
            for staff in available[:2]:
                sequence_number += 1
                staffshifts.append(StaffShift(shift_date=day, staff=staff, shift=shift_mape[sequence_number]))
                if sequence_number == 2:
                    sequence_number = 0
                person_shift_counts[staff] += 1

    return staffshifts

def generate_shifts(year: int, month: int):
    manager = Members.objects.get(email='manager@example.com')
    full_time = Members.objects.filter(position_type='full').exclude(id=manager.id).first()
    casuals = list(Members.objects.filter(position_type='casual'))

    morning = Shift.objects.filter(shift_name='Morning Shift').first()
    mid = Shift.objects.filter(shift_name='Middle Shift').first()

    week_list = generate_monthly_weeks(year, month)

    # manager and full time staff's shift
    weekdays = [week['weekdays'] for week in week_list]
    fulltime_staffshifts = []
    for weekday in weekdays:
        for day in weekday:
            fulltime_staffshifts.append(StaffShift(shift_date=day, staff=manager, shift=morning))
            fulltime_staffshifts.append(StaffShift(shift_date=day, staff=full_time, shift=mid))
    
    casual_staffshifts = casual_weekly_schedule(week_list, casuals)
    staffshifts = fulltime_staffshifts + casual_staffshifts
    
    StaffShift.objects.bulk_create(staffshifts)