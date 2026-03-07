"""
Сброс прогресса тренировок для конкретного пользователя.

По умолчанию работает в режиме dry-run.

Примеры:
    python manage.py reset_user_training_progress --username admin
    python manage.py reset_user_training_progress --username admin --apply
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.cards.models import Card
from apps.training.models import UserTrainingSettings
from apps.words.models import Word

User = get_user_model()


class Command(BaseCommand):
    help = "Reset training progress for one user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            required=True,
            help="Username to reset (example: admin)",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually apply reset (default: dry-run)",
        )

    def handle(self, *args, **options):
        username = options["username"]
        apply = options["apply"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"User '{username}' not found") from exc

        cards_qs = Card.objects.filter(user=user)
        words_qs = Word.objects.filter(user=user)

        cards_count = cards_qs.count()
        words_count = words_qs.count()
        settings_exists = UserTrainingSettings.objects.filter(user=user).exists()

        self.stdout.write("")
        self.stdout.write(self.style.WARNING("=== Training progress reset ==="))
        self.stdout.write(f"User: {user.username} (id={user.id})")
        self.stdout.write(f"Cards to reset: {cards_count}")
        self.stdout.write(f"Words to reset status: {words_count}")
        self.stdout.write(f"Training settings exists: {settings_exists}")
        self.stdout.write("")

        if not apply:
            self.stdout.write(
                self.style.WARNING("DRY RUN only. Add --apply to execute reset.")
            )
            return

        with transaction.atomic():
            updated_cards = cards_qs.update(
                ease_factor=2.5,
                interval=0,
                repetitions=0,
                lapses=0,
                consecutive_lapses=0,
                learning_step=0,
                next_review=None,
                last_review=None,
                is_in_learning_mode=True,
                is_suspended=False,
            )

            updated_words = words_qs.update(learning_status="new")

            settings_obj, _ = UserTrainingSettings.objects.get_or_create(
                user=user,
                defaults={"learning_steps": [2, 10]},
            )
            settings_obj.total_reviews = 0
            settings_obj.successful_reviews = 0
            settings_obj.last_calibration_at = 0
            settings_obj.save(
                update_fields=[
                    "total_reviews",
                    "successful_reviews",
                    "last_calibration_at",
                    "updated_at",
                ]
            )

        self.stdout.write(self.style.SUCCESS("Reset completed successfully."))
        self.stdout.write(f"Cards updated: {updated_cards}")
        self.stdout.write(f"Words updated: {updated_words}")
        self.stdout.write(
            f"Training settings counters: total_reviews={settings_obj.total_reviews}, "
            f"successful_reviews={settings_obj.successful_reviews}, "
            f"last_calibration_at={settings_obj.last_calibration_at}"
        )
