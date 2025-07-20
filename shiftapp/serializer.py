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

    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time', 'short_break', 
                  'regular_break', ]


class StaffShiftSerializer(serializers.ModelSerializer):

    class Meta:
        model = StaffShift
        fields = []


class LeaveRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveRequest
        fields = []


class LeaveBalanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveBalance
        fields = []


class WageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wage
        fields = []