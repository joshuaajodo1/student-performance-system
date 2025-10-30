"""
Django settings for student_performance_system project.
"""

from pathlib import Path
import os
import dj_database_url  # ADDED for production database connection

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# --- SECURITY AND HOSTS (UPDATED) ---
# Use environment variable for production secret key, falling back to development key
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 
    'django-insecure-h756&$7lbvsmfpj5mg3n_@m8lj-v45r8l*j=_1g&dn2n!hif&!'
)

# Set DEBUG=False when the RENDER environment variable is present
# This makes DEBUG=False in production, but True locally if RENDER is not set.
DEBUG = os.environ.get('RENDER') == None

# ALLOWED_HOSTS for production. Reads comma-separated hosts from environment variable.
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
if DEBUG:
    ALLOWED_HOSTS.append('127.0.0.1')
# --- END SECURITY AND HOSTS ---


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'performance_monitoring',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # ADDED for serving static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'student_performance_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'student_performance_system.wsgi.application'


# Database (UPDATED)
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# If DATABASE_URL is set (e.g., on Render), use it for PostgreSQL.
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600  # connection pool timeout
        )
    }
else:
    # Otherwise, use SQLite for local development.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images) (UPDATED)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# WhiteNoise storage to handle static files efficiently
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Directory where Django will collect static files for production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Any custom static directories for your apps (your original settings)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'performance_monitoring/static'),
    # Add any other project-level static directories here
]


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"