# Generated manually for Stage 1.5: WordRelation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('words', '0006_add_training_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordRelation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relation_type', models.CharField(
                    choices=[('synonym', 'Синоним'), ('antonym', 'Антоним')],
                    max_length=20,
                    verbose_name='Тип связи'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('word_from', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='relations_from',
                    to='words.word',
                    verbose_name='Исходное слово'
                )),
                ('word_to', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='relations_to',
                    to='words.word',
                    verbose_name='Связанное слово'
                )),
            ],
            options={
                'verbose_name': 'Связь между словами',
                'verbose_name_plural': 'Связи между словами',
            },
        ),
        migrations.AddConstraint(
            model_name='wordrelation',
            constraint=models.UniqueConstraint(
                fields=['word_from', 'word_to', 'relation_type'],
                name='unique_word_relation'
            ),
        ),
        migrations.AddIndex(
            model_name='wordrelation',
            index=models.Index(fields=['word_from', 'relation_type'], name='words_wordr_word_fr_idx'),
        ),
        migrations.AddIndex(
            model_name='wordrelation',
            index=models.Index(fields=['word_to', 'relation_type'], name='words_wordr_word_to_idx'),
        ),
    ]
