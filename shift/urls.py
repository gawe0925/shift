from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from shiftapp.views import MemberViewSet, ShiftViewSet, StaffShiftViewSet, LeaveRequestViewSet, LeaveBalanceViewSet, WageViewSet

router = DefaultRouter()
router.register('member', MemberViewSet, basename='member')
router.register('shift', ShiftViewSet, basename='shift')
router.register('staffshift', StaffShiftViewSet, basename='staffshift')
router.register('leaverequest', LeaveRequestViewSet, basename='leaverequest')
router.register('leavebalance', LeaveBalanceViewSet, basename='leavebalance')
router.register('wage', WageViewSet, basename='wage')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
]