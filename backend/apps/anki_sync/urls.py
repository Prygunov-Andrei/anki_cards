"""
URLs для сервера синхронизации Anki
"""
from django.urls import path
from . import views

app_name = 'anki_sync'

urlpatterns = [
    # Основной endpoint синхронизации Anki
    # Anki отправляет запросы на /sync/
    path('sync/', views.sync_endpoint, name='sync'),
    
    # API для импорта колод в синхронизацию
    path('api/sync/import/', views.import_deck_to_sync, name='import-deck'),
]

