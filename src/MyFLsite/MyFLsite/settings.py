"""
Django settings for MyFLsite project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ap1(^gw_*loimc6fsrre&b6j*bw1o(39frgc86(#z4ba^(g&5y'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
#When DEBUG = FALSE, provide admin account that will receive error messages
#ADMINS = (('admin name','admin@ma.il'),)

TEMPLATE_DEBUG = True

#General logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'logfile': {
            'level': 'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',#'logging.FileHandler'
            'maxBytes': 50000,
            'backupCount': 2,
            'filename': '/tmp/django_debug.log',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions', #Not strictly necessary but helpful for development
    'main',
    'myflq',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'MyFLsite.urls'

WSGI_APPLICATION = 'MyFLsite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'myflsitedb',
        'USER': 'myflsiteuser',
        'PASSWORD': 'myfl1234user',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Brussels'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/myflsite/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

# Media => user uploaded files
MEDIA_ROOT = '/var/www/myflsite/media/' #'/tmp/myflsite' #Absolute filesystem path to the directory that will hold user-uploaded files
    #DEPLOY# Set MEDIA_ROOT to non 'tmp' location, and MEDIA_URL to location that serves these files back
MEDIA_URL = '/media/' #'http://media.myflsite.com/' #Must end with slash if non-empty value

#Templates

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

#EMAIL
#This is only for development environment
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery settings
BROKER_URL = 'amqp://guest:guest@localhost//'
CELERY_ACCEPT_CONTENT = ['json'] #: Only add pickle to this list if your broker is secured
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
