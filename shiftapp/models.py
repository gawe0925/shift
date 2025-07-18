from decimal import Decimal
from django.db import models
from datetime import timedelta, date

from django.contrib.auth.models import AbstractUser


class Members(AbstractUser):

    POSITION_TYPES = [
        ('full', 'Full Time'),
        ('part', 'Part Time'),
        ('casual', 'Casual')
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
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    def __str__(self):
        return f"{self.first_name} + ' ' + {self.last_name}"


"""
Shift Model is for admin to identify shifts for StaffShift Model to use, for example admin can setup Morning Shift, etc.
some business might have separate shifts within one day, list restaurants, hotels.
Thus, StaffShift Model is to connect Members + Shift and use date to identify each shift.
"""
class Shift(models.Model):
    name = models.CharField(blank=True, max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    short_break = models.DurationField(default=timedelta(minutes=15))
    regular_break = models.DurationField(default=timedelta(minutes=30))


class StaffShift(models.Model):
    shift_date = models.DateField()
    staff = models.ForeignKey(Members, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    alternative_staff = models.ForeignKey(Members, on_delete=models.SET_NULL, null=True, blank=True, related_name='cover_shift')


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
    start_date = models.DateField()
    end_date = models.DateField()
    leave_hours = models.DecimalField(decimal_places=2, default=0.0, max_digits=5)
    reason = models.TextField(blank=True)
    status = models.CharField(choices=STATUS_CHOICES, default='pending', max_length=10)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(Members, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')

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

    DURATION = [
        ('week', 'Weekly'),
        ('fort', 'Fortnightly'),
        ('mon', 'Monthly'),
    ]

    staff = models.ForeignKey(Members, on_delete=models.CASCADE)
    shift = models.ForeignKey(StaffShift, on_delete=models.CASCADE)
    start_date = models.DateField()
    pay_duration = models.CharField(choices=DURATION, default='fortnight', max_length=10)
    pay_rate = models.DecimalField(decimal_places=2, default=26.55, max_digits=5)

    @property
    def end_date(self):
        if self.pay_duration == 'week':
            return self.start_date + timedelta(6)
        elif self.pay_duration == 'fort':
            return self.start_date + timedelta(13)
        else:
            # for monthly payment
            small = [4, 6, 9, 11]
            big = [1, 3, 5, 7, 8, 10, 12]

            if self.start_date.month in big:
                return self.start_date + timedelta(30)
            elif self.start_date.month in small:
                return self.start_date + timedelta(29)
            else:
                return self.start_date + timedelta(27)