from django.urls import path
from rest_framework.routers import DefaultRouter

from market.views.user_views import RegisterAccount, ConfirmAccount, LoginAccount, AccountDetails, \
    ContactView, ResetPassword, ResetPasswordConfirm
from market.views.shop_views import MarketView, BasketView, OrderView
from market.views.partner_views import PartnerUpdate, PartnerState, PartnerOrders

router = DefaultRouter()
router.register('market', MarketView)
router.register('user/contact', ContactView)
router.register('partner/orders', PartnerOrders, basename='Order')

urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
    path('user/login', LoginAccount.as_view(), name='user-login'),

    path('user/password_reset', ResetPassword.as_view(), name='password-reset'),
    path('user/password_reset/confirm', ResetPasswordConfirm.as_view(), name='password-reset-confirm'),

    path('user/details', AccountDetails.as_view(), name='user-details'),

    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),

    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),

] + router.urls
