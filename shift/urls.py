from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from shiftapp.views import PasswordResetRequestView, PasswordResetConfirmView, PasswordResetTokenValidateView
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
    path('api/', include(router.urls)),
    
    # JWT 認證端點
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 密碼重設 API
    path('api/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('api/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/password-reset/validate/', PasswordResetTokenValidateView.as_view(), name='password_reset_validate'),
]