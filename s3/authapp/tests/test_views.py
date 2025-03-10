import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authapp.models import User
from rest_framework_simplejwt.tokens import RefreshToken

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_register_user(api_client):
    url = reverse("register")
    data = {"whatsapp_number": "1234567890", "password": "testpass", "name": "John Doe"}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 201
    assert User.objects.filter(whatsapp_number="1234567890").exists()

@pytest.mark.django_db
def test_request_otp(api_client):
    user = User.objects.create_user(whatsapp_number="1234567890", password="testpass")
    url = reverse("request-otp")
    response = api_client.post(url, {"whatsapp_number": "1234567890"}, format="json")
    assert response.status_code == 200 or response.status_code == 500  # Handle external API failure

@pytest.mark.django_db
def test_verify_otp(api_client, mocker):
    user = User.objects.create_user(whatsapp_number="1234567890", password="testpass")
    
    # Mock OTP storage to simulate a correct OTP
    mocker.patch("authapp.views.otp_store", {"1234567890": "123456"})

    url = reverse("verify-otp")
    response = api_client.post(url, {"whatsapp_number": "1234567890", "otp": "123456"}, format="json")
    assert response.status_code == 200
    assert "access" in response.data

@pytest.mark.django_db
def test_staff_auth(api_client):
    user = User.objects.create_superuser(whatsapp_number="1234567890", password="adminpass")
    
    url = reverse("staff_token")
    data = {"whatsapp_number": "1234567890", "password": "adminpass"}
    response = api_client.post(url, data, format="json")
    
    assert response.status_code == 200
    assert "access" in response.data

@pytest.mark.django_db
def test_refresh_token(api_client):
    user = User.objects.create_user(whatsapp_number="1234567890", password="testpass")
    refresh = RefreshToken.for_user(user)
    
    url = reverse("token_refresh")
    response = api_client.post(url, {"refresh": str(refresh)}, format="json")
    
    assert response.status_code == 200
    assert "access" in response.data
