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

# Prompt endpoints
prompt_urlpatterns = [
    path('prompts/', views.get_user_prompts_view, name='get-user-prompts'),
    path('prompts/<str:prompt_type>/', views.get_user_prompt_view, name='get-user-prompt'),
    path('prompts/<str:prompt_type>/update/', views.update_user_prompt_view, name='update-user-prompt'),
    path('prompts/<str:prompt_type>/reset/', views.reset_user_prompt_view, name='reset-user-prompt'),
]

# Word analysis endpoints (Этап 6)
analysis_urlpatterns = [
    path('analyze-words/', views.analyze_words_view, name='analyze-words'),
    path('translate-words/', views.translate_words_view, name='translate-words'),
    path('process-german-words/', views.process_german_words_view, name='process-german-words'),
]

# Deck management endpoints (Этап 7)
deck_urlpatterns = [
    path('decks/', views.deck_list_create_view, name='deck-list-create'),
    path('decks/<int:deck_id>/', views.deck_detail_view, name='deck-detail'),
    path('decks/<int:deck_id>/add_words/', views.deck_add_words_view, name='deck-add-words'),
    path('decks/<int:deck_id>/remove_word/', views.deck_remove_word_view, name='deck-remove-word'),
    path('decks/<int:deck_id>/words/<int:word_id>/', views.deck_update_word_view, name='deck-update-word'),
    path('decks/<int:deck_id>/generate/', views.deck_generate_apkg_view, name='deck-generate'),
]

# Token endpoints (Этап 9)
token_urlpatterns = [
    path('tokens/balance/', views.get_token_balance_view, name='token-balance'),
    path('tokens/transactions/', views.get_token_transactions_view, name='token-transactions'),
    path('tokens/add/', views.add_tokens_view, name='token-add'),
]

