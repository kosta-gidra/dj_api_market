import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dj_api_diplom.settings')

app = Celery('dj_api_diplom')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks()

