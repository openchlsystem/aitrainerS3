from .base import *

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['your-production-domain.com']

# Production Database Configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "production_db_name",
        "USER": "production_db_user",
        "PASSWORD": "production_db_password",
        "HOST": "production_db_host",
        "PORT": "",
    }
}

# Stricter security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True