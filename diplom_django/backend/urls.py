from django.urls import path
from .views import RegisterAccountView, ConfirmEmailView, AccountDetailsView, LoginAccountView, ContactView, \
    CategoryView, ShopView, BasketView, OrderView, PartnerOrdersView, PartnerStatusView, PartnerUpdateView, \
    ProductInfoView, upload_goods
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm


app_name = 'backend'

urlpatterns = [
    path('user/register/', RegisterAccountView.as_view(), name='user-register'),
    path('user/register/confirm/', ConfirmEmailView.as_view(), name='email-confirm'),
    path('user/details/', AccountDetailsView.as_view(), name='account-details'),
    path('user/login/', LoginAccountView.as_view(), name='user-login'),
    path('user/contact/', ContactView.as_view(), name='user-contact'),
    path('user/password-reset/', reset_password_request_token, name='reset-password'),
    path('user/password-reset/confirm/', reset_password_confirm, name='reset-password-confirm'),
    path('partner/status/', PartnerStatusView.as_view(), name='partner-status'),
    path('partner/orders/', PartnerOrdersView.as_view(), name='partner-orders'),
    path('partner/update/', PartnerUpdateView.as_view(), name='partner-update'),
    path('categories/', CategoryView.as_view(), name='categories'),
    path('shops/', ShopView.as_view(), name='shops'),
    path('products/', ProductInfoView.as_view(), name='products'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('order/', OrderView.as_view(), name='order'),
    path('upload_goods/', upload_goods, name='upload_goods'),
]
