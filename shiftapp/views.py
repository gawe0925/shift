import logging as log
from datetime import datetime
from django.conf import settings
from django.db.models import Sum
from rest_framework import status
from django.db.models import Max, Min
from django.core.mail import send_mail
from rest_framework.views import APIView
from django.utils.encoding import force_str
from rest_framework.response import Response
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .utils import calculate_end_date
from .permissions import IsAdminOrReadyOnly
from .tokens import FiveMinuteTokenGenerator
from .models import Members, Shift, StaffShift, LeaveRequest, LeaveBalance, Wage
from .serializer import MemberSerializer, ShiftSerializer, StaffShiftSerializer, LeaveRequestSerializer, LeaveBalanceSerializer, WageSerializer

# universal function
def str_to_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return False


class MemberViewSet(ModelViewSet):
    queryset = Members.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            if user.is_superuser:
                return Members.objects.all()
            return Members.objects.exclude(is_superuser=True)
        return Members.objects.filter(id=user.id)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


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
            if user.is_superuser:
                return LeaveRequest.objects.all()
            return LeaveRequest.objects.exclude(staff__is_superuser=True)
        return LeaveRequest.objects.filter(staff__id=user.id)
    
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class LeaveBalanceViewSet(ModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadyOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LeaveBalance.objects.all()
        return LeaveBalance.objects.filter(staff=user)


class WageViewSet(ModelViewSet):
    queryset = Wage.objects.all()
    serializer_class = WageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Wage.objects.all() if user.is_superuser else Wage.objects.filter(staff=user)
    

    def list(self, request, *args, **kwargs):

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        duration = request.query_params.get('duration')
        staff_id = request.query_params.get('staff_id')

        start_date = str_to_date(start_date_str)
        end_date = str_to_date(end_date_str)

        if not start_date:
            return Response({'start_date': 'required'}, status=400)

        if not end_date and duration:
            end_date = calculate_end_date(start_date, duration)

        if not end_date:
            return Response({'end_date': 'required or unable to calculate'}, status=400)

        if request.user.is_superuser and staff_id:
            queryset = self.get_queryset().filter(
                shift_date__gte=start_date,
                shift_date__lte=end_date,
                staff__id = staff_id
            )

        else:
            queryset = self.get_queryset().filter(
                shift_date__gte=start_date,
                shift_date__lte=end_date
            )

        if not queryset:
            today = datetime.today().date()

            return Response({'search_period': f'from {start_date} to {end_date}',
                             'messsage': 'No data in selected period',
                             'valid_date_from': today,
                             'valid_date_til': today,
                            }, status=200)
        else:
            shift_date_max = str(Wage.objects.aggregate(Max('shift_date'))['shift_date__max'] or '')
            shift_date_min = str(Wage.objects.aggregate(Min('shift_date'))['shift_date__min'] or '')
            days = len(queryset)

            if days and days == 1:
                day_str = f'{days}_day_salary'
            elif days and days > 1:
                day_str = f'{days}_days_salary'
            total_salary = queryset.aggregate(total_salary=Sum('salary'))['total_salary']

            serializer = self.get_serializer(queryset, many=True)

            return Response({'shift_detail': serializer.data,
                            day_str: round(total_salary, 2),
                            'search_period': f'from {start_date} to {end_date}',
                            'valid_date_from': shift_date_min,
                            'valid_date_til': shift_date_max,
                            }, status=200)


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