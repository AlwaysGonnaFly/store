from pathlib import Path

from pyqiwip2p import QiwiP2P
from yoomoney import Client

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-p&*#$YY(*H$jrphf+*jdr*o@wgkil%f4w@(sjr^0ei4ims590!y3@wp@w6o5g6'

DEBUG = False

ALLOWED_HOSTS = [
    '127.0.0.1', 'вашip',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dbname',
        'USER': 'uname',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

QIWI_SECRET_KEY = 'KEY'
P2P = QiwiP2P(auth_key=QIWI_SECRET_KEY)

YOOMONEY_WALLET = 'WALLET'
YOOMONEY_TOKEN = 'TOKEN'
YOOMONEY_CLIENT = Client(token=YOOMONEY_TOKEN)
