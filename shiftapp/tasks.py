from celery import shared_task
from datetime import datetime, timedelta
from models import *
from django.db.models import F, Q
import logging as log

@shared_task
def calculate_daily_salary():
    yesterday = datetime.now().date() - timedelta(days=1)

    print(f"start counting {yesterday}'s empolyee wages")
    log.info(f"start counting {yesterday}'s empolyee wages")
    
    log.info(f"filter {yesterday}'s StaffShift")
    shifts = StaffShift.objects.filter(shift_date=yesterday, has_payslip=False)
    if not shifts:
        log.info(f"{yesterday}'s StaffShift does not exist")
        return True
    wage = []
    casual_rate = Decimal('1.25')
    for s in shifts:
        employee = s.staff if not s.cover_shift else s.alternative_staff
        work_hours = s.shift.daily_work_hours()
        pay_rate = employee.pay_rate
        if employee.position_type == 'casual':
            pay_rate = employee.pay_rate * casual_rate
        wage.append(Wage(staff=employee, shift=s, 
                         salary=work_hours*pay_rate, 
                         shift_date=yesterday))

    log.info(f"start generate {yesterday}'s Wage")
    Wage.objects.bulk_create(wage)
    print(f"{yesterday}'s wages have been generated")
    log.info(f"{yesterday}'s wages have been generated")
    
    log.info(f"start mark off {yesterday}'s StaffShift")
    shifts.update(has_payslip=True)
    print(f"mark off {yesterday}'s StaffShift")
    log.info(f"mark off {yesterday}'s StaffShift")

    log.info(f"{yesterday} - finalised")
    return True