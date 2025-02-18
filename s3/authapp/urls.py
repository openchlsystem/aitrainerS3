from django.urls import path
from .views import RefreshAccessTokenView, RegisterUserView, RequestOTPView, VerifyOTPView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path("request-otp/", RequestOTPView.as_view(), name="request-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("refresh-token/", RefreshAccessTokenView.as_view(), name="refresh-token"),
]


