from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.training_settings_view, name='training-settings'),
    path('settings/reset/', views.training_settings_reset_view, name='training-settings-reset'),
    path('settings/defaults/', views.training_settings_defaults_view, name='training-settings-defaults'),
    # ЭТАП 6: Training API
    path('session/', views.training_session_view, name='training-session'),
    path('answer/', views.training_answer_view, name='training-answer'),
    path('enter-learning/', views.training_enter_learning_view, name='training-enter-learning'),
    path('exit-learning/', views.training_exit_learning_view, name='training-exit-learning'),
    path('stats/', views.training_stats_view, name='training-stats'),
    # Дашборд тренировок и активация
    path('dashboard/', views.training_dashboard_view, name='training-dashboard'),
    path('deck/<int:deck_id>/activate/', views.training_deck_activate_view, name='training-deck-activate'),
    path('deck/<int:deck_id>/deactivate/', views.training_deck_deactivate_view, name='training-deck-deactivate'),
    path('category/<int:category_id>/activate/', views.training_category_activate_view, name='training-category-activate'),
    path('category/<int:category_id>/deactivate/', views.training_category_deactivate_view, name='training-category-deactivate'),
    # ЭТАП 7: AI Generation API
    path('generate-etymology/', views.generate_etymology_view, name='generate-etymology'),
    path('generate-hint/', views.generate_hint_view, name='generate-hint'),
    path('generate-sentence/', views.generate_sentence_view, name='generate-sentence'),
    path('generate-synonym/', views.generate_synonym_view, name='generate-synonym'),
    # ЭТАП 13: Notifications API
    path('notifications/settings/', views.notification_settings_view, name='notification-settings'),
    path('notifications/check/', views.notification_check_view, name='notification-check'),
    # ЭТАП 14: Forgetting Curves
    path('forgetting-curve/', views.forgetting_curve_view, name='forgetting-curve'),
]
