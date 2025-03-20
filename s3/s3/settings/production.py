from .base import *

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['edms-enpoints.bitz-itc.com', '192.168.8.13']

# Production Database Configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "aitraining_data",
        "USER":"root",
        "HOST":"localhost",
        "PASSWORD":"2025Ai@2025!",
        "PORT":"",
    #    'OPTIONS': {
    #         'unix_socket': '/var/lib/mysql/mysql.sock',  
    #     },
    }
}

# Stricter security settings
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True