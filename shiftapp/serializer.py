from rest_framework import serializers
from .models import Members, Shift, StaffShift, LeaveRequest, LeaveBalance, Wage


class MemberSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request', None)
        user = request.user
        part_time_staff = Members.objects.filter(id=user.id, position_type='part').first()

        if not part_time_staff:
            self.fields.pop('part_time_rate', None)
    
    class Meta:
        model = Members
        fields = ['first_name', 'last_name', 'email', 'mobile',
                  'permanent_position', 'part_time_rate', 'position_type',]


class ShiftSerializer(serializers.ModelSerializer):
    daily_work_hours = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time', 'short_break', 
                  'regular_break', 'daily_work_hours']
        
    def get_daily_work_hours(self, obj):
        return round(obj.daily_work_hours(), 2)


class StaffShiftSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    alternative_staff_name = serializers.SerializerMethodField()
    shift = serializers.StringRelatedField()
    class Meta:
        model = StaffShift
        fields = ["shift_date", "staff", "staff_name", "shift", "cover_shift",
                  "alternative_staff", "alternative_staff_name"]
        
    
    def get_staff_name(self, obj):
        return str(obj.staff)
    
    def get_alternative_staff_name(self,obj):
        return str(obj.alternative_staff)
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if not instance.cover_shift:
            rep.pop('cover_shift', None)
            rep.pop("alternative_staff", None)
            rep.pop('alternative_staff_name', None)

        return rep


class LeaveRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveRequest
        fields = '__all__'


class LeaveBalanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveBalance
        fields = '__all__'


class WageSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request', None)
        user =  request.user
        if not user.is_staff:
            self.fields.pop('staff')

    class Meta:
        model = Wage
        fields = ['staff', 'start_date', 'pay_duration']