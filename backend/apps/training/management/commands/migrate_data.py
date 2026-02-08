"""
Этап 11: Безопасная миграция данных.

Создаёт Card для каждого Word (у которого нет Card),
создаёт UserTrainingSettings для каждого пользователя,
обновляет learning_status слов.

БЕЗОПАСНА: не удаляет и не изменяет существующие данные.
Можно запускать повторно (идемпотентна).

Использование:
  python manage.py migrate_data            # preview (dry run)
  python manage.py migrate_data --apply    # apply changes
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.words.models import Word
from apps.cards.models import Card
from apps.training.models import UserTrainingSettings

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate existing data: create Cards from Words, create TrainingSettings for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually apply changes (default is dry-run preview)',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        mode = 'APPLYING' if apply else 'DRY RUN (use --apply to execute)'
        self.stdout.write(f'\n=== Data Migration — {mode} ===\n')

        # 1. Create UserTrainingSettings
        users = User.objects.all()
        settings_created = 0
        for user in users:
            exists = UserTrainingSettings.objects.filter(user=user).exists()
            if not exists:
                if apply:
                    UserTrainingSettings.objects.create(
                        user=user,
                        age_group='adult',
                        learning_steps=[2, 10],
                    )
                settings_created += 1
                self.stdout.write(f'  [Settings] Create for user: {user.username}')

        self.stdout.write(
            f'\nUserTrainingSettings: {settings_created} to create '
            f'(existing: {UserTrainingSettings.objects.count()})\n'
        )

        # 2. Create Cards from Words
        words_without_cards = Word.objects.exclude(
            id__in=Card.objects.values_list('word_id', flat=True)
        )
        total_words = words_without_cards.count()
        self.stdout.write(f'Words without Cards: {total_words}\n')

        cards_to_create = []
        words_to_update_status = []

        for word in words_without_cards.select_related('user'):
            card_type = word.card_type or 'normal'
            is_auxiliary = card_type in ('empty', 'cloze')

            cards_to_create.append(Card(
                user=word.user,
                word=word,
                card_type=card_type,
                is_auxiliary=is_auxiliary,
                is_in_learning_mode=True,
                ease_factor=2.5,
                interval=0,
                repetitions=0,
                lapses=0,
                consecutive_lapses=0,
                learning_step=0,
                next_review=timezone.now(),
            ))
            words_to_update_status.append(word.id)

        if not apply:
            # Show preview
            by_type = {}
            for c in cards_to_create:
                by_type[c.card_type] = by_type.get(c.card_type, 0) + 1
            for ct, count in sorted(by_type.items()):
                self.stdout.write(f'  Card type={ct}: {count}')

            self.stdout.write(
                f'\nTotal Cards to create: {len(cards_to_create)}'
            )
            self.stdout.write(
                f'Words to update learning_status → "learning": {len(words_to_update_status)}'
            )
            self.stdout.write(
                f'\n*** DRY RUN — no changes made. Use --apply to execute. ***\n'
            )
            return

        # Apply with transaction
        self.stdout.write('\nApplying changes in a single transaction...\n')
        with transaction.atomic():
            # Bulk create cards
            if cards_to_create:
                Card.objects.bulk_create(cards_to_create, batch_size=500)
                self.stdout.write(
                    self.style.SUCCESS(f'  Created {len(cards_to_create)} Cards')
                )

            # Update learning_status for words that got cards
            if words_to_update_status:
                updated = Word.objects.filter(
                    id__in=words_to_update_status,
                    learning_status='new',
                ).update(learning_status='learning')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Updated {updated} Words: learning_status → "learning"'
                    )
                )

        # Summary
        self.stdout.write(f'\n=== Migration complete ===')
        self.stdout.write(f'  Users: {User.objects.count()}')
        self.stdout.write(f'  Words: {Word.objects.count()}')
        self.stdout.write(f'  Cards: {Card.objects.count()}')
        self.stdout.write(f'  TrainingSettings: {UserTrainingSettings.objects.count()}')
        self.stdout.write('')
