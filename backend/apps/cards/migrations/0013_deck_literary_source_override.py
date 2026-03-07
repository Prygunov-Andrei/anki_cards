from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0012_add_literary_source_to_deck'),
    ]

    operations = [
        migrations.AddField(
            model_name='deck',
            name='literary_source_override',
            field=models.BooleanField(default=False, verbose_name='Переопределение литературного источника'),
        ),
    ]
