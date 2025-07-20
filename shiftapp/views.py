from django.conf import settings
from rest_framework import status
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
    queryset = StaffShift.objects.select_related('member', 'shift').all()
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
            return LeaveBalance.objects.all()
        return LeaveBalance.objects.filter(id=user.id)


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