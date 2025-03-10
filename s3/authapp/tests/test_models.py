import pytest
from authapp.models import User

@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(whatsapp_number="1234567890", password="securepass")
    assert user.whatsapp_number == "1234567890"
    assert user.check_password("securepass")
    assert user.is_active
    assert not user.is_staff

@pytest.mark.django_db
def test_create_superuser():
    user = User.objects.create_superuser(whatsapp_number="0987654321", password="adminpass")
    assert user.whatsapp_number == "0987654321"
    assert user.check_password("adminpass")
    assert user.is_active
    assert user.is_staff

@pytest.mark.django_db
def test_generate_otp():
    user = User.objects.create_user(whatsapp_number="1122334455", password="testpass")
    otp = user.generate_otp()
    assert isinstance(otp, str)
    assert len(otp) == 6  # Assuming a 6-digit OTP
