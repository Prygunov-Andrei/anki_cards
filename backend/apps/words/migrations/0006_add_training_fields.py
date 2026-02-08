# Generated manually for Stage 1: Word Refactoring

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('words', '0005_fix_all_card_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='etymology',
            field=models.TextField(blank=True, default='', help_text='Происхождение слова, генерируется автоматически', verbose_name='Этимология'),
        ),
        migrations.AddField(
            model_name='word',
            name='sentences',
            field=models.JSONField(blank=True, default=list, help_text='Формат: [{"text": "...", "source": "ai|user"}]', verbose_name='Примеры предложений'),
        ),
        migrations.AddField(
            model_name='word',
            name='notes',
            field=models.TextField(blank=True, default='', verbose_name='Заметки пользователя'),
        ),
        migrations.AddField(
            model_name='word',
            name='hint_text',
            field=models.TextField(blank=True, default='', help_text='Описание слова без перевода, на изучаемом языке', verbose_name='Текстовая подсказка'),
        ),
        migrations.AddField(
            model_name='word',
            name='hint_audio',
            field=models.FileField(blank=True, null=True, upload_to='hints/', verbose_name='Аудио подсказка'),
        ),
        migrations.AddField(
            model_name='word',
            name='part_of_speech',
            field=models.CharField(blank=True, choices=[('noun', 'Существительное'), ('verb', 'Глагол'), ('adjective', 'Прилагательное'), ('adverb', 'Наречие'), ('pronoun', 'Местоимение'), ('preposition', 'Предлог'), ('conjunction', 'Союз'), ('interjection', 'Междометие'), ('article', 'Артикль'), ('numeral', 'Числительное'), ('particle', 'Частица'), ('other', 'Другое')], default='', max_length=20, verbose_name='Часть речи'),
        ),
        migrations.AddField(
            model_name='word',
            name='stickers',
            field=models.JSONField(blank=True, default=list, help_text='Эмоции/наклейки: ["❤️", "⭐", "🔥"]', verbose_name='Стикеры'),
        ),
        migrations.AddField(
            model_name='word',
            name='learning_status',
            field=models.CharField(choices=[('new', 'Новое'), ('learning', 'В изучении'), ('reviewing', 'На повторении'), ('mastered', 'Освоено')], default='new', max_length=20, verbose_name='Статус обучения'),
        ),
        migrations.AddIndex(
            model_name='word',
            index=models.Index(fields=['user', 'learning_status'], name='words_word_user_id_learning_idx'),
        ),
    ]
