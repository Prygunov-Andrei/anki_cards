from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_cards_view, name='generate-cards'),
    path('download/<uuid:file_id>/', views.download_cards_view, name='download-cards'),
]

# Media endpoints
media_urlpatterns = [
    path('generate-image/', views.generate_image_view, name='generate-image'),
    path('generate-audio/', views.generate_audio_view, name='generate-audio'),
    path('upload-image/', views.upload_image_view, name='upload-image'),
    path('upload-audio/', views.upload_audio_view, name='upload-audio'),
]

