"""
Management-команда для миграции legacy-инвертированных Word-объектов на Card-level.

Legacy-подход создавал новые Word-объекты со swap-нутыми полями при инвертировании.
Корректный подход (Stage 3): создавать Card(card_type='inverted') для того же Word.

Эта команда:
1. Находит все Word-ы с card_type='inverted'
2. Для каждого находит оригинальный Word (original_word == inverted.translation)
3. Создаёт Card(card_type='inverted') для оригинального Word
4. Удаляет legacy-инвертированный Word из всех колод
5. Удаляет legacy-инвертированный Word

Использование:
    python manage.py migrate_inverted_words           # Dry run (предварительный просмотр)
    python manage.py migrate_inverted_words --apply    # Выполнить миграцию
"""
import logging
from django.core.management.base import BaseCommand
from apps.words.models import Word
from apps.cards.models import Card

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Мигрирует legacy-инвертированные Word-объекты в Card-объекты'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            default=False,
            help='Выполнить миграцию (по умолчанию — dry run)',
        )
        parser.add_argument(
            '--user',
            type=str,
            default=None,
            help='Мигрировать только для указанного пользователя (username)',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        username_filter = options['user']

        if not apply:
            self.stdout.write(self.style.WARNING(
                '\n=== DRY RUN (предварительный просмотр) ===\n'
                'Добавьте --apply для выполнения миграции.\n'
            ))

        # Находим все legacy-инвертированные Word-ы
        inverted_words = Word.objects.filter(card_type='inverted')
        if username_filter:
            inverted_words = inverted_words.filter(user__username=username_filter)

        inverted_words = inverted_words.select_related('user').prefetch_related('decks')

        total = inverted_words.count()
        self.stdout.write(f'Найдено legacy-инвертированных Word-ов: {total}')

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Нечего мигрировать.'))
            return

        migrated = 0
        card_created = 0
        card_existed = 0
        no_original = 0
        errors = 0

        for inv_word in inverted_words:
            try:
                # Инвертированный Word: original_word = перевод, translation = исходное слово
                # Ищем оригинальный Word: original_word == inv_word.translation
                original_candidates = Word.objects.filter(
                    user=inv_word.user,
                    original_word=inv_word.translation,
                    translation=inv_word.original_word,
                ).exclude(card_type='inverted')

                if not original_candidates.exists():
                    # Пробуем более мягкий поиск (без точного совпадения translation)
                    original_candidates = Word.objects.filter(
                        user=inv_word.user,
                        original_word=inv_word.translation,
                    ).exclude(card_type='inverted')

                original_word = original_candidates.first()

                if not original_word:
                    self.stdout.write(self.style.WARNING(
                        f'  [!] Не найден оригинал для inv_word #{inv_word.id} '
                        f'"{inv_word.original_word}" -> "{inv_word.translation}" '
                        f'(user: {inv_word.user.username})'
                    ))
                    no_original += 1
                    continue

                # Проверяем, есть ли уже инвертированная Card для оригинала
                existing_card = Card.objects.filter(
                    user=inv_word.user,
                    word=original_word,
                    card_type='inverted'
                ).exists()

                if existing_card:
                    card_existed += 1
                    status_msg = 'Card уже существует'
                else:
                    card_created += 1
                    status_msg = 'Card будет создан'

                decks_list = list(inv_word.decks.values_list('name', flat=True))

                self.stdout.write(
                    f'  [{migrated + 1}/{total}] inv_word #{inv_word.id} '
                    f'"{inv_word.original_word}" -> original #{original_word.id} '
                    f'"{original_word.original_word}" | {status_msg} | '
                    f'Колоды: {", ".join(decks_list) if decks_list else "нет"}'
                )

                if apply:
                    # 1. Создаём Card(card_type='inverted') для оригинального Word
                    if not existing_card:
                        Card.create_inverted(original_word)
                        logger.info(
                            f'Создана Card(inverted) для Word #{original_word.id} '
                            f'"{original_word.original_word}" (миграция из Word #{inv_word.id})'
                        )

                    # 2. Удаляем inv_word из всех колод
                    for deck in inv_word.decks.all():
                        deck.words.remove(inv_word)

                    # 3. Удаляем связанные Card-ы inv_word (если есть)
                    Card.objects.filter(word=inv_word).delete()

                    # 4. Удаляем legacy-инвертированный Word
                    inv_word.delete()

                migrated += 1

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(
                    f'  [ERR] Ошибка при обработке inv_word #{inv_word.id}: {str(e)}'
                ))
                logger.exception(f'Ошибка миграции inv_word #{inv_word.id}')

        self.stdout.write('\n--- Итоги ---')
        self.stdout.write(f'Всего legacy-инвертированных: {total}')
        self.stdout.write(f'Обработано: {migrated}')
        self.stdout.write(f'Card-ов создано: {card_created}')
        self.stdout.write(f'Card-ы уже существовали: {card_existed}')
        self.stdout.write(f'Не найден оригинал: {no_original}')
        self.stdout.write(f'Ошибок: {errors}')

        if apply:
            self.stdout.write(self.style.SUCCESS(
                f'\nМиграция выполнена. Удалено {migrated} legacy Word-ов.'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '\nЭто был dry run. Добавьте --apply для выполнения миграции.'
            ))
