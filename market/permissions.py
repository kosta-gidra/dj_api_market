from rest_framework.permissions import BasePermission
from django.utils.translation import gettext_lazy as _


class IsShop(BasePermission):
    message = _('Only for shops')

    def has_permission(self, request, view):
        return request.user.type == 'shop'

