from __future__ import absolute_import, unicode_literals

# 匯入剛剛建立的 celery app
from .celery import app as celery_app

__all__ = ['celery_app']