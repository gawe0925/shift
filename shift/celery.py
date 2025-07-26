from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 設定 Django 的預設 settings 模組
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shift.settings')

# 建立 Celery 實例
app = Celery('shift')

# 從 Django 設定檔讀取 Celery 的設定（用 DJANGO_SETTINGS_MODULE）
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自動載入所有 app 中的 tasks.py
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
