from django.conf import settings
from rest_framework import status
from django.core.mail import send_mail
from rest_framework.views import APIView
from datetime import datetime, timedelta
from django.utils.encoding import force_str
from rest_framework.response import Response
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .permissions import IsAdminOrReadyOnly
from .tokens import FiveMinuteTokenGenerator
from .models import Members, Shift, StaffShift, LeaveRequest, LeaveBalance, Wage
from .serializer import MemberSerializer, ShiftSerializer, StaffShiftSerializer, LeaveRequestSerializer, LeaveBalanceSerializer, WageSerializer


class MemberViewSet(ModelViewSet):
    queryset = Members.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Members.objects.all()
        return Members.objects.filter(id=user.id).first()

    def get_object(self):
        user = self.request.user
        obj = super().get_object()
        # permission control
        if not user.is_staff and obj != user:
            raise PermissionDenied('Access Denied')
        return obj

    def partial_update(self, request, *args, **kwargs):
        # fliter queryset with user's info
        instance = self.get_object()
        # partially update request data
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        # if update result is not valid, then raise error message 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

class ShiftViewSet(ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadyOnly]


class StaffShiftViewSet(ModelViewSet):
    queryset = StaffShift.objects.select_related('staff', 'shift', 'alternative_staff').all()
    serializer_class = StaffShiftSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadyOnly]


class LeaveRequestViewSet(ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LeaveBalance.objects.all()
        return LeaveBalance.objects.filter(id=user.id)


class LeaveBalanceViewSet(ModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadyOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LeaveBalance.objects.all()
        return LeaveBalance.objects.filter(id=user.id)
    

class WageViewSet(ModelViewSet):
    queryset = Wage.objects.all()
    serializer_class = WageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Wage.objects.all()
        return Wage.objects.filter(id=user.id)
    
    def create(self, *args, **kwargs):

        def str_to_date(string):
            return datetime.strptime(string, "%Y-%m-%d").date()

        def end_date(start_date, dura):
            if dura == 'week':
                return (start_date + timedelta(6)).date()
            elif dura == 'fort':
                return (start_date + timedelta(13)).date()
            else:
                # for monthly payment
                small = [4, 6, 9, 11]
                big = [1, 3, 5, 7, 8, 10, 12]

                if start_date.month in big:
                    return (start_date + timedelta(30)).date()
                elif start_date.month in small:
                    return (start_date + timedelta(29)).date()
                else:
                    return (start_date + timedelta(27)).date()
        
        today = datetime.today().date()
        data = self.request.data
        data_copy = data.copy()
        start_day = data.get('start_date', None)
        if start_day:
            start_day = str_to_date(start_day)
        end_day = data.get('end_day', None)
        if end_day:
            end_day = str_to_date(end_day)
            if end_day > today:
                return Response('message: End_day greater than today', status=400)

        duration = data.get('pay_duration', None)
        staff = self.request.user
        if start_day and duration:
            end_day = end_date(start_day, duration)

        total_shifts = StaffShift.objects.select_related('shift', 'staff', 
                                                         'alternative_staff'
                                                         ).filter(staff=staff, 
                                                            shift_date__gte=start_day, 
                                                            shift_date__lte=end_day
                                                            ).exclude(cover_shift=True)
        
        total_shifts = None
        if not total_shifts:
            data_copy['wage'] = 0
            data_copy['staff'] = staff.__str__()
            return Response(data_copy)
        for s in total_shifts:
            dhs = s.shift.daily_work_hours()
            pay_rate = s._wage_set().first().pay_rate
        

        return Response(data)


# use email to change and verify password 
User = get_user_model()
token_generator = FiveMinuteTokenGenerator()


class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required.'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_link = f"https://your-frontend-domain.com/reset-password/{uid}/{token}/"

        send_mail(
            'Reset your password',
            f'Click the link to reset your password: {reset_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )

        return Response({'detail': 'Password reset email sent.'}, status=200)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not (uidb64 and token and new_password):
            return Response({'detail': 'Missing data.'}, status=400)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Invalid UID.'}, status=400)

        if not token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Password has been reset.'}, status=200)


class PasswordResetTokenValidateView(APIView):
    def get(self, request):
        uidb64 = request.query_params.get('uid')
        token = request.query_params.get('token')

        if not uidb64 or not token:
            return Response({'valid': False, 'detail': 'Missing parameters.'}, status=400)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'valid': False}, status=400)

        if token_generator.check_token(user, token):
            return Response({'valid': True})
        else:
            return Response({'valid': False}, status=400)