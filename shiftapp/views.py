from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .permissions import IsAdminOrReadyOnly
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
        return Members.objects.filter(id=user.id)

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
    queryset = StaffShift.objects.all()
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
        return LeaveBalance.objects.filter(id=user.id).first()
    

class WageViewSet(ModelViewSet):
    queryset = Wage.objects.all()
    serializer_class = WageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LeaveBalance.objects.all()
        return LeaveBalance.objects.filter(id=user.id)