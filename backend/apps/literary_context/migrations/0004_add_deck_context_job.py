import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('literary_context', '0003_add_text_metadata'),
        ('cards', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeckContextJob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('progress', models.IntegerField(default=0, help_text='0-100 percent')),
                ('current_word', models.CharField(blank=True, default='', max_length=200)),
                ('stats', models.JSONField(blank=True, default=dict)),
                ('unmatched_words', models.JSONField(blank=True, default=list)),
                ('error_message', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='context_jobs', to='cards.deck')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='context_jobs', to='literary_context.literarysource')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='context_jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Deck Context Job',
                'verbose_name_plural': 'Deck Context Jobs',
                'ordering': ['-created_at'],
            },
        ),
    ]
