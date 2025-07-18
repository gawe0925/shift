from rest_framework.permissions import BasePermission, SAFE_METHODS

# permission control
class IsAdminOrReadyOnly(BasePermission):
    def has_permission(self, request, view):
        # SAFE_METHODS : Get
        if request.method in SAFE_METHODS:
            return True
        else:
            # admin access only
            return request.user.is_staff