from django.urls import path
from . import views

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════
    # WORDS
    # ═══════════════════════════════════════════════════════════════
    
    # Список слов
    path('list/', views.words_list_view, name='words-list'),
    
    # Детали слова (со связями)
    path('<int:word_id>/', views.word_detail_view, name='word-detail'),
    
    # Связи слова (синонимы/антонимы)
    path('<int:word_id>/relations/', views.word_relations_view, name='word-relations'),
    path('<int:word_id>/add-synonym/', views.word_add_synonym_view, name='word-add-synonym'),
    path('<int:word_id>/add-antonym/', views.word_add_antonym_view, name='word-add-antonym'),
    path('<int:word_id>/relations/<int:relation_id>/', views.word_delete_relation_view, name='word-delete-relation'),
    
    # Категории слова
    path('<int:word_id>/categories/', views.word_categories_view, name='word-categories'),
    
    # ═══════════════════════════════════════════════════════════════
    # CARDS (Этап 3)
    # ═══════════════════════════════════════════════════════════════
    
    # Все карточки слова
    path('<int:word_id>/cards/', views.word_cards_list_view, name='word-cards-list'),
    
    # Создание карточек разных типов
    path('<int:word_id>/cards/inverted/', views.card_create_inverted_view, name='card-create-inverted'),
    path('<int:word_id>/cards/empty/', views.card_create_empty_view, name='card-create-empty'),
    path('<int:word_id>/cards/cloze/', views.card_create_cloze_view, name='card-create-cloze'),
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORIES
    # ═══════════════════════════════════════════════════════════════
    
    # Список/создание категорий
    path('categories/', views.categories_list_view, name='categories-list'),
    
    # Детали/обновление/удаление категории
    path('categories/<int:category_id>/', views.category_detail_view, name='category-detail'),
    
    # Слова в категории
    path('categories/<int:category_id>/words/', views.category_words_view, name='category-words'),
    
    # ═══════════════════════════════════════════════════════════════
    # ЭТАП 8: Words Catalog API
    # ═══════════════════════════════════════════════════════════════
    
    # Статистика
    path('<int:word_id>/stats/', views.word_stats_view, name='word-stats'),
    path('stats/', views.words_stats_view, name='words-stats'),
    
    # Действия
    path('<int:word_id>/enter-learning/', views.word_enter_learning_view, name='word-enter-learning'),
    path('bulk-action/', views.words_bulk_action_view, name='words-bulk-action'),
]

