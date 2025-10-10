# app_estoque/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/historico/$', consumers.HistoricoConsumer.as_asgi()),
]