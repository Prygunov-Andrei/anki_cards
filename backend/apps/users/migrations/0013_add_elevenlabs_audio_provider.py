from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_update_gemini_model_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='audio_provider',
            field=models.CharField(
                choices=[
                    ('elevenlabs', 'ElevenLabs'),
                    ('openai', 'OpenAI TTS'),
                    ('gtts', 'Google TTS (gTTS)'),
                ],
                default='openai',
                max_length=20,
                verbose_name='Провайдер генерации аудио',
            ),
        ),
    ]
