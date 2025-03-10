from django.urls import reverse, resolve
from authapp.views import RegisterUserView, RequestOTPView, VerifyOTPView, StaffAuthView
from rest_framework_simplejwt.views import TokenRefreshView

def test_register_url():
    assert resolve(reverse("register")).func.view_class == RegisterUserView

def test_request_otp_url():
    assert resolve(reverse("request-otp")).func.view_class == RequestOTPView

def test_verify_otp_url():
    assert resolve(reverse("verify-otp")).func.view_class == VerifyOTPView

def test_refresh_token_url():
    assert resolve(reverse("token_refresh")).func.view_class == TokenRefreshView

def test_staff_token_url():
    assert resolve(reverse("staff_token")).func.view_class == StaffAuthView
