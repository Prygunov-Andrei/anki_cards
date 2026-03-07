from django.urls import path
from . import views

urlpatterns = [
    path('sources/', views.sources_list_view, name='literary-sources'),
    path('generate/', views.generate_context_view, name='literary-generate'),
    path('generate-batch/', views.generate_batch_context_view, name='literary-generate-batch'),
    path('generate-deck-context/', views.generate_deck_context_view, name='literary-generate-deck-context'),
    path('word/<int:word_id>/media/', views.word_context_media_view, name='literary-word-media'),
    # Reader API
    path('sources/<slug:source_slug>/texts/', views.texts_list_view, name='literary-texts-list'),
    path('sources/<slug:source_slug>/texts/<slug:text_slug>/', views.text_detail_view, name='literary-text-detail'),
    path('word-from-reader/', views.word_from_reader_view, name='literary-word-from-reader'),
]
