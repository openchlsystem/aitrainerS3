from django.db import models

# Create your models here.
import pyotp
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, whatsapp_number, password=None, **extra_fields):
        """
        Creates and saves a User with the given whatsapp_number and password.
        """
        if not whatsapp_number:
            raise ValueError("The WhatsApp number field must be set")

        user = self.model(
            whatsapp_number=whatsapp_number, **extra_fields
        )  # include the extra fields.
        if password:
            user.set_password(password)  # Set the password using the built-in method
        user.save(using=self._db)
        return user

    def create_superuser(self, whatsapp_number, password=None):
        """Create and return a superuser with the given details."""
        user = self.create_user(whatsapp_number=whatsapp_number, password=password)
        user.is_active = (
            True  # You may also set other superuser flags like is_staff, is_superuser
        )
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    whatsapp_number = models.CharField(max_length=15, unique=True)
    otp_secret = models.CharField(max_length=32, default=pyotp.random_base32)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) 
    first_name = models.CharField(
        max_length=100, null=True, blank=True
    )  # Add this field for name

    objects = UserManager()

    USERNAME_FIELD = "whatsapp_number"

    def generate_otp(self):
        return pyotp.TOTP(self.otp_secret).now()
