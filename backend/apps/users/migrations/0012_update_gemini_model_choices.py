from django.db import migrations, models


def update_gemini_model(apps, schema_editor):
    """Update existing users with old model name to new one."""
    User = apps.get_model('users', 'User')
    User.objects.filter(gemini_model='nano-banana-pro-preview').update(
        gemini_model='gemini-3.1-flash-image-preview'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_add_image_style'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='gemini_model',
            field=models.CharField(
                choices=[
                    ('gemini-2.5-flash-image', 'Gemini Flash (быстрая, 0.5 токена)'),
                    ('gemini-3.1-flash-image-preview', 'NanoBanana-2 (новая, 1 токен)'),
                ],
                default='gemini-2.5-flash-image',
                max_length=50,
                verbose_name='Модель Gemini для генерации изображений',
            ),
        ),
        migrations.RunPython(update_gemini_model, migrations.RunPython.noop),
    ]
