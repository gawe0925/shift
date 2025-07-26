from decimal import Decimal
from django.db import models
from datetime import timedelta, date, datetime

from django.contrib.auth.models import AbstractUser


class Members(AbstractUser):

    POSITION_TYPES = [
        ('full', 'Full Time'),
        ('part', 'Part Time'),
        ('casual', 'Casual'),
        ('admin', 'admin')
    ]

    gender = models.CharField(blank=False, max_length=50)
    email = models.EmailField(unique=True, max_length=100)
    mobile = models.CharField(blank=False, max_length=50)
    address = models.CharField(blank=False, max_length=50)
    suburb = models.CharField(blank=False, max_length=50)
    state = models.CharField(blank=False, max_length=50)
    postcode = models.CharField(blank=False, max_length=50)
    tfn = models.CharField(blank=False, max_length=50)
    permanent_position = models.BooleanField(default=False)
    part_time_rate = models.DecimalField(blank=True, decimal_places=2, default=1.0, max_digits=5)
    position_type = models.CharField(choices=POSITION_TYPES, default='casual', max_length=50)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    pay_rate = models.DecimalField(decimal_places=2, default=26.55, max_digits=5)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # reserved fields for potential future expansion
    undefined_1 = models.CharField(blank=True, max_length=200)
    undefined_2 = models.CharField(blank=True, max_length=200)
    undefined_3 = models.CharField(blank=True, max_length=200)
    undefined_4 = models.CharField(blank=True, max_length=200)
    undefined_5 = models.CharField(blank=True, max_length=200)


    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email


"""
Shift Model is for admin to identify shifts for StaffShift Model to use, for example admin can setup Morning Shift, etc.
some business might have separate shifts within one day, list restaurants, hotels.
Thus, StaffShift Model is to connect Members + Shift and use date to identify each shift.
"""
class Shift(models.Model):

    BREAK_CHOICES = [
        ('none', 'No Break'),
        ('15min', 'Break 15 Minutes'),
        ('30min', 'Break 30 Minutes'),
    ]

    BREAK_OPTIONS = {
        'none': timedelta(minutes=0),
        '15min': timedelta(minutes=15),
        '30min': timedelta(minutes=30)
    }

    shift_name = models.CharField(blank=True, max_length=50)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    break_min = models.CharField(choices=BREAK_CHOICES, default='none', max_length=10)

    # reserved fields for potential future expansion
    undefined_1 = models.CharField(blank=True, max_length=200)
    undefined_2 = models.CharField(blank=True, max_length=200)
    undefined_3 = models.CharField(blank=True, max_length=200)
    undefined_4 = models.CharField(blank=True, max_length=200)
    undefined_5 = models.CharField(blank=True, max_length=200)

    def daily_work_duration(self):
        if self.start_time and self.end_time:
            # 先算時間差
            start_t = datetime.combine(datetime.min, self.start_time)
            end_t = datetime.combine(datetime.min, self.end_time)
            work_time = end_t - start_t
            # 減掉休息時間
            work_time -= self.break_time
            return work_time if work_time > timedelta(0) else timedelta(0)
        return timedelta(0)

    @property
    def break_time(self):
        return self.BREAK_OPTIONS[self.break_min]
    
    def daily_work_hours(self):
        # 以小時為單位 (浮點數)
        td = self.daily_work_duration()
        return Decimal(td.total_seconds() / 3600)
    
    def __str__(self):
        return f"{self.shift_name} ({self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}, {self.get_break_min_display()})"


class StaffShift(models.Model):
    shift_date = models.DateField()
    staff = models.ForeignKey(Members, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    cover_shift = models.BooleanField(default=False)
    alternative_staff = models.ForeignKey(Members, on_delete=models.SET_NULL, null=True, blank=True, related_name='cover_shift')
    has_payslip = models.BooleanField(default=False)

    # reserved fields for potential future expansion
    undefined_1 = models.CharField(blank=True, max_length=200)
    undefined_2 = models.CharField(blank=True, max_length=200)
    undefined_3 = models.CharField(blank=True, max_length=200)
    undefined_4 = models.CharField(blank=True, max_length=200)
    undefined_5 = models.CharField(blank=True, max_length=200)

    def staff_position(self):
        if self.staff:
            if self.staff.position_type == 'full' and self.staff.is_staff:
                return f'Manager'
            elif self.staff.position_type == 'part':
                return f'{self.staff.position_type} {round(self.staff.part_time_rate, 1)}'
            else:
                return f'{self.staff.position_type}'
            

class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('personal', 'Personal Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('no', 'No Show'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled'),
    ]

    staff = models.ForeignKey(Members, on_delete=models.CASCADE)
    leave_type = models.CharField(choices=LEAVE_TYPES, max_length=20)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    leave_hours = models.DecimalField(decimal_places=2, default=0.0, max_digits=5)
    reason = models.TextField(blank=True)
    status = models.CharField(choices=STATUS_CHOICES, default='pending', max_length=10)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(Members, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')

    # reserved fields for potential future expansion
    undefined_1 = models.CharField(blank=True, max_length=200)
    undefined_2 = models.CharField(blank=True, max_length=200)
    undefined_3 = models.CharField(blank=True, max_length=200)
    undefined_4 = models.CharField(blank=True, max_length=200)
    undefined_5 = models.CharField(blank=True, max_length=200)

    def __str__(self):
        return f"{self.staff} - {self.leave_type} ({self.start_date} ~ {self.end_date})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not is_new:
            old = LeaveRequest.objects.get(pk=self.pk)
            if old.status == 'pending' and self.status == 'approved':
                # status changed: pending ➜ approved
                self.update_leave_balance(deduct=True)

            elif old.status == 'approved' and self.status == 'canceled':
                # status changed: approved ➜ canceled
                self.update_leave_balance(deduct=False)

        super().save(*args, **kwargs)

    def update_leave_balance(self, deduct=True):
        balance, _ = LeaveBalance.objects.get_or_create(staff=self.staff)
        hours = self.leave_hours

        if self.leave_type == 'annual':
            balance.annual_leave_used += hours if deduct else -hours
        elif self.leave_type == 'sick':
            balance.sick_leave_used += hours if deduct else -hours

        balance.save()


class LeaveBalance(models.Model):
    staff = models.OneToOneField(Members, on_delete=models.CASCADE)
    annual_leave_used = models.DecimalField(decimal_places=2, default=0.0, max_digits=5)
    sick_leave_used = models.DecimalField(decimal_places=2, default=0.0, max_digits=5)

    # reserved fields for potential future expansion
    undefined_1 = models.CharField(blank=True, max_length=200)
    undefined_2 = models.CharField(blank=True, max_length=200)
    undefined_3 = models.CharField(blank=True, max_length=200)
    undefined_4 = models.CharField(blank=True, max_length=200)
    undefined_5 = models.CharField(blank=True, max_length=200)

    def get_available_annual_leave_hours(self):
        """
        根據 start_date 計算累積的年假時數
        全職一年 = 20 天 × 7.6 小時 = 152 小時
        每月累積 152 / 12 = 12.67 小時
        """
        if not self.staff.start_date:
            return Decimal('0.0')
        elif self.staff.end_date:
            return Decimal('0.0')
        elif not self.staff.permanent_position:
            return Decimal('0.0')

        today = date.today()
        months_worked = (today.year - self.staff.start_date.year) * 12 + (today.month - self.staff.start_date.month)
        accrued = Decimal(months_worked) * Decimal('12.67')

        if self.staff.position_type == 'part':
            return max(accrued * self.staff.part_time_rate - self.annual_leave_used, 0)
        return max(accrued - self.annual_leave_used, 0)

    def get_available_sick_leave_hours(self):
        """
        根據 start_date 計算累積的病假時數
        全職一年 = 10 天 × 7.6 小時 = 76 小時
        每月累積 76 / 12 = 6.33 小時
        """
        if not self.staff.start_date:
            return Decimal('0.0')
        elif self.staff.end_date:
            return Decimal('0.0')
        elif not self.staff.permanent_position:
            return Decimal('0.0')

        today = date.today()
        months_worked = (today.year - self.staff.start_date.year) * 12 + (today.month - self.staff.start_date.month)
        accrued = Decimal(months_worked) * Decimal('6.33')

        if self.staff.position_type == 'Part Time':
            return max(accrued * self.staff.part_time_rate - self.annual_leave_used, 0)
        return max(accrued - self.annual_leave_used, 0)   

    def __str__(self):
        return f"{self.staff} - Annual leave hrs:{self.get_available_annual_leave_hours()}, Sick leave hrs:{self.get_available_sick_leave_hours()}"
    

class Wage(models.Model):
    staff = models.ForeignKey(Members, on_delete=models.CASCADE)
    shift = models.ForeignKey(StaffShift, on_delete=models.CASCADE)
    shift_date = models.DateField(null=True, blank=True)
    pay_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(decimal_places=2, default=0, max_digits=5)

    # reserved fields for potential future expansion
    undefined_1 = models.CharField(blank=True, max_length=200)
    undefined_2 = models.CharField(blank=True, max_length=200)
    undefined_3 = models.CharField(blank=True, max_length=200)
    undefined_4 = models.CharField(blank=True, max_length=200)
    undefined_5 = models.CharField(blank=True, max_length=200)