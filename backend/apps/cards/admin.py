from django.contrib import admin
from .models import GeneratedDeck, UserPrompt, Deck, PartOfSpeechCache, Token, TokenTransaction, Card


@admin.register(GeneratedDeck)
class GeneratedDeckAdmin(admin.ModelAdmin):
    """Административная панель для модели GeneratedDeck"""
    list_display = ['deck_name', 'user', 'cards_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['deck_name', 'user__username']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'deck_name', 'cards_count')
        }),
        ('Файл', {
            'fields': ('file_path',)
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )


@admin.register(UserPrompt)
class UserPromptAdmin(admin.ModelAdmin):
    """Административная панель для модели UserPrompt"""
    list_display = ['user', 'prompt_type', 'is_custom', 'updated_at']
    list_filter = ['prompt_type', 'is_custom', 'updated_at']
    search_fields = ['user__username', 'prompt_type']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'prompt_type', 'is_custom')
        }),
        ('Промпт', {
            'fields': ('custom_prompt',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PartOfSpeechCache)
class PartOfSpeechCacheAdmin(admin.ModelAdmin):
    """Административная панель для модели PartOfSpeechCache"""
    list_display = ['word', 'language', 'part_of_speech', 'article', 'created_at']
    list_filter = ['language', 'part_of_speech', 'created_at']
    search_fields = ['word', 'part_of_speech']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('word', 'language', 'part_of_speech', 'article')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    """Административная панель для модели Deck"""
    list_display = ['name', 'user', 'target_lang', 'source_lang', 'words_count', 'updated_at']
    list_filter = ['target_lang', 'source_lang', 'created_at', 'updated_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['words']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'name', 'cover', 'target_lang', 'source_lang')
        }),
        ('Слова', {
            'fields': ('words',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    """Административная панель для модели Token (баланс токенов)"""
    list_display = ['user', 'balance', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'balance')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['add_100_tokens', 'add_500_tokens']
    
    @admin.action(description='Начислить 100 токенов')
    def add_100_tokens(self, request, queryset):
        for token in queryset:
            token.balance += 100
            token.save()
            TokenTransaction.objects.create(
                user=token.user,
                transaction_type='earned',
                amount=100,
                description='Начислено администратором'
            )
        self.message_user(request, f'Начислено 100 токенов {queryset.count()} пользователям')
    
    @admin.action(description='Начислить 500 токенов')
    def add_500_tokens(self, request, queryset):
        for token in queryset:
            token.balance += 500
            token.save()
            TokenTransaction.objects.create(
                user=token.user,
                transaction_type='earned',
                amount=500,
                description='Начислено администратором'
            )
        self.message_user(request, f'Начислено 500 токенов {queryset.count()} пользователям')


@admin.register(TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin):
    """Административная панель для истории транзакций токенов"""
    list_display = ['user', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['user', 'transaction_type', 'amount', 'description', 'created_at']
    
    def has_add_permission(self, request):
        return False  # Запрещаем добавление вручную
    
    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем изменение


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """Административная панель для модели Card"""
    list_display = [
        'id', 'word', 'card_type', 'user',
        'ease_factor', 'interval', 'next_review',
        'is_in_learning_mode', 'is_auxiliary', 'is_suspended',
    ]
    list_filter = [
        'card_type', 'is_in_learning_mode', 
        'is_auxiliary', 'is_suspended',
    ]
    search_fields = ['word__original_word', 'word__translation']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'word']
    
    fieldsets = (
        ('Основное', {
            'fields': ('user', 'word', 'card_type')
        }),
        ('Cloze', {
            'fields': ('cloze_sentence', 'cloze_word_index'),
            'classes': ('collapse',),
        }),
        ('SM-2 Параметры', {
            'fields': (
                'ease_factor', 'interval', 'repetitions',
                'lapses', 'consecutive_lapses', 'learning_step',
            )
        }),
        ('Планирование', {
            'fields': ('next_review', 'last_review')
        }),
        ('Статусы', {
            'fields': ('is_in_learning_mode', 'is_auxiliary', 'is_suspended')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
