from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,)
from .views import RegisterUserView, RequestOTPView, VerifyOTPView, StaffAuthView



urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path("request-otp/", RequestOTPView.as_view(), name="request-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("refresh-token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("staff-token/", StaffAuthView.as_view(), name="staff_token"),
]


