import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dj_api_market.settings')

app = Celery('dj_api_market')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks()

