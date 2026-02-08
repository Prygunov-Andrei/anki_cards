from django.contrib import admin
from .models import UserTrainingSettings, NotificationSettings


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_frequency', 'browser_notifications_enabled', 'last_notified_at']
    list_filter = ['notification_frequency', 'browser_notifications_enabled']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at', 'last_notified_at']


@admin.register(UserTrainingSettings)
class UserTrainingSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'age_group', 'starting_ease', 'interval_modifier',
        'total_reviews', 'successful_reviews', 'target_retention'
    ]
    list_filter = ['age_group', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_reviews', 'successful_reviews', 'last_calibration_at']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user', 'age_group')
        }),
        ('Ease Factor', {
            'fields': ('starting_ease', 'min_ease_factor')
        }),
        ('Дельты EF', {
            'fields': ('again_ef_delta', 'hard_ef_delta', 'good_ef_delta', 'easy_ef_delta')
        }),
        ('Модификаторы интервалов', {
            'fields': ('interval_modifier', 'hard_interval_modifier', 'easy_bonus')
        }),
        ('Шаги обучения', {
            'fields': ('learning_steps', 'graduating_interval', 'easy_interval')
        }),
        ('Настройки сессии', {
            'fields': ('default_session_duration',)
        }),
        ('Пороги', {
            'fields': ('lapse_threshold', 'stability_threshold', 'calibration_interval', 'target_retention')
        }),
        ('Калибровка', {
            'fields': ('total_reviews', 'successful_reviews', 'last_calibration_at'),
            'classes': ('collapse',),
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
