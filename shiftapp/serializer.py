from decimal import Decimal
from django.utils import timezone
from django.db.models import Max, Min
from rest_framework import serializers
from datetime import datetime, timedelta
from .models import Members, Shift, StaffShift, LeaveRequest, LeaveBalance, Wage


class MemberSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request', None)
        user = request.user
        part_time_staff = Members.objects.filter(id=user.id, position_type='part').first()

        if not part_time_staff:
            self.fields.pop('part_time_rate', None)
    
    class Meta:
        model = Members
        fields = ['id', 'first_name', 'last_name', 'email', 'mobile',
                  'permanent_position', 'part_time_rate', 'position_type', 
                  'is_active', 'is_staff', 'is_superuser', 'password']
        read_only_fields = ['id', 'is_superuser']

    def create(self, validated_data):
        # 找出 Demo 的 manager account 禁止 Demo 帳號去新增 User
        requested_user = self.context['request'].user
        if requested_user.email == 'manager@shift.com' and not requested_user.is_superuser:
            raise serializers.ValidationError({
                "error": "Demo account cannot create new member"
            })

        password = validated_data.pop('password', None)
        user = Members(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        requested_user = self.context['request'].user
        if 'is_active' in validated_data and validated_data['is_active'] is False:
            # 防止停用管理員帳戶
            if instance.is_superuser:
                raise serializers.ValidationError({
                    "is_active": "Cannot deactivate admin accounts"
                })
            # 防止經理自己停用自己
            if instance.is_staff and instance == requested_user:
                raise serializers.ValidationError({
                    "is_active": "Cannot deactivate yourself"
                })
        
        password = validated_data.pop('password', None)
        # 允許所有字段更新（移除之前可能的限制）
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ShiftSerializer(serializers.ModelSerializer):
    daily_work_hours = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = ['id', 'shift_name', 'start_time', 'end_time', 
                  'daily_work_hours']
        read_only_fields = ['id']
        
    def get_daily_work_hours(self, obj):
        return round(obj.daily_work_hours(), 2)


class StaffShiftSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    alternative_staff_name = serializers.SerializerMethodField()
    shift_name = serializers.StringRelatedField()
    class Meta:
        model = StaffShift
        fields = ['id', "shift_date", "staff", "staff_name", "shift", "shift_name", 
                  "cover_shift", "alternative_staff", "alternative_staff_name"]
        read_only_fields = ['id']
        
    def get_shift_name(self, obj):
        return str(obj.shift)

    def get_staff_name(self, obj):
        return str(obj.staff)
    
    def get_alternative_staff_name(self, obj):
        return str(obj.alternative_staff)
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if not instance.cover_shift:
            rep.pop('cover_shift', None)
            rep.pop("alternative_staff", None)
            rep.pop('alternative_staff_name', None)

        return rep
    
    def validate(self, data):

        cover_shift = data.get('cover_shift')
        if cover_shift:
            alt_staff_id = data.get('alternative_staff')
            if not alt_staff_id:
                raise serializers.ValidationError({'alternative_staff': 'alternative_staff is required'})
        
        return data


class LeaveRequestSerializer(serializers.ModelSerializer):
    staff = serializers.StringRelatedField()
    reviewed_by = serializers.StringRelatedField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request', None)
        if request:
            user = request.user
            if user.is_staff:
                pass
            else:
                self.fields.pop('reviewed_by', None)

    class Meta:
        model = LeaveRequest
        fields = ['id', 'staff', 'leave_type', 'start_date', 'end_date', 
                  'leave_hours', 'reason', 'status', 'requested_at', 
                  'reviewed_at', 'reviewed_by']
        read_only_fields = ['id']
        
    def validate(self, data):
        request = self.context['request']
        user = request.user

        # 如果是更新操作且只更新狀態，跳過其他驗證
        if self.instance and len(data) == 1 and 'status' in data:
            return data

        # 以下驗證只在創建新請假申請時執行
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        reason = data.get('reason')
        leave_hours = data.get('leave_hours')

        if not start_date:
            raise serializers.ValidationError({'start_date': 'start_date is required'})
        if not end_date:
            raise serializers.ValidationError({'end_date': 'end_date is required'})
        if not leave_hours:
            raise serializers.ValidationError({'leave_hours': 'leave_hours is required'})
        elif leave_hours <= 0:
            raise serializers.ValidationError({'leave_hours': 'must greater than zero'})
        if not data.get('leave_type'):
            raise serializers.ValidationError({'leave_type': 'leave_type is required'})
        if start_date > end_date:
            raise serializers.ValidationError('start_date later than end_date')
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # 查詢重複請假
        existing = LeaveRequest.objects.filter(
            staff=user,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status__in=['pending', 'approved']
        )
        if existing.exists():
            raise serializers.ValidationError('An existing leave request matches this period.')

        return data
    
    def create(self, validated_data):
        validated_data['staff'] = self.context['request'].user
        validated_data['status'] = 'pending'

        return super().create(validated_data)
    
    def validate_status(self, value):
        valid_status = ['approved', 'rejected', 'canceled']
        if value not in valid_status:
            raise serializers.ValidationError("Invalid status value.")
        return value
    
    def update(self, instance, validated_data):
        request = self.context['request']
        user = request.user
        review_status = ['approved', 'rejected']

        current_status = instance.status
        new_status = validated_data.get('status', None)

        if not new_status:
            raise serializers.ValidationError("status is required")
        
        if current_status == 'pending' and new_status in review_status:
            if not user.is_staff:
                raise serializers.ValidationError("Only manager can review leave requests.")
            elif instance.staff == user:
                raise serializers.ValidationError("You cannot review your own leave request.")
            
        if current_status == 'approved' and new_status != 'canceled':
            raise serializers.ValidationError("Approved requests can only be canceled.")

        instance.status = new_status
        instance.reviewed_by = user
        instance.reviewed_at = timezone.now()
        instance.save()

        return instance


class LeaveBalanceSerializer(serializers.ModelSerializer):
    staff = serializers.StringRelatedField()
    available_annual_leave_hours = serializers.SerializerMethodField()
    available_sick_leave_hours = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = ['staff', 'available_annual_leave_hours', 
                  'available_sick_leave_hours']

    def get_available_annual_leave_hours(self, obj):
        return str(obj.get_available_annual_leave_hours())

    def get_available_sick_leave_hours(self, obj):
        return str(obj.get_available_sick_leave_hours())


class WageSerializer(serializers.ModelSerializer):
    staff = serializers.StringRelatedField()
    shift = serializers.StringRelatedField()

    class Meta:
        model = Wage
        fields = ['id', 'staff', 'shift', 'pay_date', 'salary']
        read_only_fields = ['id']

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if not instance.pay_date:
            rep.pop('pay_date', None)

        return rep
    
    # def get_shift_date_max(self, obj):
    #     return str(Wage.objects.aggregate(Max('shift_date'))['shift_date__max'] or '')

    # def get_shift_date_min(self, obj):
    #     return str(Wage.objects.aggregate(Min('shift_date'))['shift_date__min'] or '')