from rest_framework import serializers
from .models import Members, Shift, StaffShift, LeaveRequest, LeaveBalance, Wage


class MemberSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Members
        fields = []


class ShiftSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shift
        fields = []


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