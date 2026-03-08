from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_add_elevenlabs_audio_provider'),
    ]

    operations = [
        # LLM models
        migrations.AddField(
            model_name='user',
            name='hint_generation_model',
            field=models.CharField(default='gpt-4o-mini', max_length=50, verbose_name='Модель для подсказок'),
        ),
        migrations.AddField(
            model_name='user',
            name='scene_description_model',
            field=models.CharField(default='gpt-4o-mini', max_length=50, verbose_name='Модель для описания сцен'),
        ),
        migrations.AddField(
            model_name='user',
            name='matching_model',
            field=models.CharField(default='gpt-4o', max_length=50, verbose_name='Модель для матчинга'),
        ),
        migrations.AddField(
            model_name='user',
            name='keyword_extraction_model',
            field=models.CharField(default='gpt-4o-mini', max_length=50, verbose_name='Модель для ключевых слов'),
        ),
        # Temperatures
        migrations.AddField(
            model_name='user',
            name='hint_temperature',
            field=models.FloatField(default=0.8, verbose_name='Температура подсказок'),
        ),
        migrations.AddField(
            model_name='user',
            name='scene_description_temperature',
            field=models.FloatField(default=0.5, verbose_name='Температура описания сцен'),
        ),
        migrations.AddField(
            model_name='user',
            name='matching_temperature',
            field=models.FloatField(default=0.2, verbose_name='Температура матчинга'),
        ),
        migrations.AddField(
            model_name='user',
            name='keyword_temperature',
            field=models.FloatField(default=0.3, verbose_name='Температура ключевых слов'),
        ),
        # ElevenLabs voice
        migrations.AddField(
            model_name='user',
            name='elevenlabs_voice_id',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='ElevenLabs Voice ID'),
        ),
        # Prompt templates
        migrations.AddField(
            model_name='user',
            name='hint_prompt_template',
            field=models.TextField(blank=True, default='', verbose_name='Шаблон промпта подсказок'),
        ),
        migrations.AddField(
            model_name='user',
            name='scene_description_prompt',
            field=models.TextField(blank=True, default='', verbose_name='Промпт описания сцен'),
        ),
        migrations.AddField(
            model_name='user',
            name='keyword_extraction_prompt',
            field=models.TextField(blank=True, default='', verbose_name='Промпт ключевых слов'),
        ),
        migrations.AddField(
            model_name='user',
            name='image_prompt_template',
            field=models.TextField(blank=True, default='', verbose_name='Шаблон промпта изображений'),
        ),
    ]
