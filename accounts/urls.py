from django.urls import path
from .views import (
    RegisterView, VerifyEmailView, VerifyEmailResendView, LoginView, LogoutView,CheckAuthView, UserProfileView,PasswordResetRequestView, 
    PasswordResetResendView, PasswordResetVerifyView, PasswordResetCompleteView, 
    DeviceRenewalRequestView,DeviceRenewalVerifyView,DeviceRenewalCompleteView, 
    PasswordChangeView, CompanyCreateView,MyCompanyView ,CompanyUpdateView, CompanyListView
    , CompanyDeleteView, UserListView, DefinedDeviceCreateView, 
    DefinedDeviceUpdate,DefinedDeviceListView,DefinedDeviceDetailView,DefinedDeviceDeleteView,
    ExpoPushTokenCreateView, ExpoPushTokenUpdate, ExpoPushTokenListView,
    AuditLogListView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('verify-email-resend/', VerifyEmailResendView.as_view(), name='verify-email-resend'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('check-auth/', CheckAuthView.as_view(), name='check-auth'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-resend/', PasswordResetResendView.as_view(), name='password-reset-resend'),
    path('password-reset-verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password-reset-complete'),
    path('device-renewal-request/', DeviceRenewalRequestView.as_view(), name='device-renewal-request'),
    path('device-renewal-verify/', DeviceRenewalVerifyView.as_view(), name='device-renewal-verify'),
    path('device-renewal-complete/', DeviceRenewalCompleteView.as_view(), name='device-renewal-complete'),
    path('password-change/', PasswordChangeView.as_view(), name='password-change'),
    path('company-create/', CompanyCreateView.as_view(), name='company-create'),
    path('my-company/', MyCompanyView.as_view(), name='my-company'),
    path('company-update/', CompanyUpdateView.as_view(), name='company-update'),
    path('company-list/', CompanyListView.as_view(), name='company-list'),
    path('company-delete/<id>/', CompanyDeleteView.as_view(), name='company-delete'),
    path('user-list/', UserListView.as_view(), name='user-list'),
    path('defined-device-create/', DefinedDeviceCreateView.as_view(), name='defined-device-create'),
    path('defined-device-update/', DefinedDeviceUpdate.as_view(), name='defined-device-update'),
    path('defined-device-list/', DefinedDeviceListView.as_view(), name='defined-device-list'),
    path('defined-device-detail/', DefinedDeviceDetailView.as_view(), name='defined-device-detail'),
    path('defined-device-delete/', DefinedDeviceDeleteView.as_view(), name='defined-device-delete'),
    path('expo-push-token-create/', ExpoPushTokenCreateView.as_view(), name='expo-push-token-create'),
    path('expo-push-token-update/', ExpoPushTokenUpdate.as_view(), name='expo-push-token-update'),
    path('expo-push-token-list/', ExpoPushTokenListView.as_view(), name='expo-push-token-list'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit-logs'),
    

] 