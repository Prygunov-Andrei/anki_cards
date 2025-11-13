from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_cards_view, name='generate-cards'),
    path('download/<uuid:file_id>/', views.download_cards_view, name='download-cards'),
]

