# Generated manually for Stage 2: Category

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('words', '0007_wordrelation'),
    ]

    operations = [
        # 1. Создаём модель Category
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('icon', models.CharField(blank=True, default='', help_text='Эмодзи (например: 🍎, 🚗, 🐕)', max_length=10, verbose_name='Иконка')),
                ('order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='children',
                    to='words.category',
                    verbose_name='Родительская категория'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='categories',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь'
                )),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'ordering': ['order', 'name'],
            },
        ),
        
        # 2. Уникальный constraint
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                fields=['user', 'name', 'parent'],
                name='unique_category_name_per_parent'
            ),
        ),
        
        # 3. Индекс
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['user', 'parent'], name='words_categ_user_pa_idx'),
        ),
        
        # 4. Добавляем M2M поле в Word
        migrations.AddField(
            model_name='word',
            name='categories',
            field=models.ManyToManyField(
                blank=True,
                related_name='words',
                to='words.category',
                verbose_name='Категории'
            ),
        ),
    ]
