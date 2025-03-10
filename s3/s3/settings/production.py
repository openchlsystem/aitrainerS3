from .base import *

# Production settings
DEBUG = False
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "your-production-domain.com").split(",")

# Production Database Configuration (MySQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "production_db_name"),
        "USER": os.getenv("DB_USER", "production_db_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "production_db_password"),
        "HOST": os.getenv("DB_HOST", "production_db_host"),
        "PORT": os.getenv("DB_PORT", "3306"),  # Default MySQL port
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
