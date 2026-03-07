"""
Клонирование пользовательских данных между аккаунтами.

Копирует:
- Категории (со структурой parent/child)
- Слова (с AI-контентом)
- Медиа-файлы слов (image/audio/hint_audio) как независимые копии
- Связи слов (синонимы/антонимы)
- Колоды и связи deck.words
- Карточки (normal/inverted/empty/cloze) с reset прогресса

По умолчанию dry-run. Для выполнения используйте --apply.

Примеры:
  python manage.py clone_user_data --source admin --target Liudmila --target-password Liudmila
  python manage.py clone_user_data --source admin --target Liudmila --target-password Liudmila --apply
"""

import os
import uuid
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.cards.models import Card, Deck
from apps.training.models import UserTrainingSettings
from apps.words.models import Category, Word, WordRelation

User = get_user_model()


def _copy_filefield(source_field, target_prefix: str) -> Optional[str]:
    """
    Создаёт независимую копию файла в хранилище и возвращает новый путь.
    """
    if not source_field:
        return None
    source_name = getattr(source_field, "name", None)
    if not source_name:
        return None
    if not default_storage.exists(source_name):
        return None

    _, ext = os.path.splitext(source_name)
    filename = f"{target_prefix}/{uuid.uuid4().hex}{ext.lower()}"

    with default_storage.open(source_name, "rb") as src:
        content = src.read()
    saved_name = default_storage.save(filename, ContentFile(content))
    return saved_name


class Command(BaseCommand):
    help = "Clone all user data (decks/words/cards/media) from source user to target user"

    def add_arguments(self, parser):
        parser.add_argument("--source", type=str, required=True, help="Source username")
        parser.add_argument("--target", type=str, required=True, help="Target username")
        parser.add_argument(
            "--target-password",
            type=str,
            required=True,
            help="Password for target user (created or updated)",
        )
        parser.add_argument(
            "--replace-target-data",
            action="store_true",
            help="Allow replacing existing target data if target already has words/decks/cards/categories",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually apply cloning (default is dry-run)",
        )

    def handle(self, *args, **options):
        source_username = options["source"]
        target_username = options["target"]
        target_password = options["target_password"]
        replace_target_data = options["replace_target_data"]
        apply = options["apply"]

        try:
            source_user = User.objects.get(username=source_username)
        except User.DoesNotExist as exc:
            raise CommandError(f"Source user '{source_username}' not found") from exc

        target_user = User.objects.filter(username=target_username).first()
        target_exists = target_user is not None

        source_categories = Category.objects.filter(user=source_user)
        source_words = Word.objects.filter(user=source_user)
        source_decks = Deck.objects.filter(user=source_user)
        source_cards = Card.objects.filter(user=source_user)
        source_relations = WordRelation.objects.filter(
            word_from__user=source_user,
            word_to__user=source_user,
        )

        self.stdout.write("")
        self.stdout.write(self.style.WARNING("=== Clone user data ==="))
        self.stdout.write(f"Source: {source_user.username} (id={source_user.id})")
        self.stdout.write(f"Target: {target_username} ({'exists' if target_exists else 'new'})")
        self.stdout.write(f"Categories: {source_categories.count()}")
        self.stdout.write(f"Words: {source_words.count()}")
        self.stdout.write(f"Cards: {source_cards.count()}")
        self.stdout.write(f"Decks: {source_decks.count()}")
        self.stdout.write(f"Word relations: {source_relations.count()}")
        self.stdout.write("")

        if target_exists:
            target_words = Word.objects.filter(user=target_user).count()
            target_cards = Card.objects.filter(user=target_user).count()
            target_decks = Deck.objects.filter(user=target_user).count()
            target_categories = Category.objects.filter(user=target_user).count()
            has_data = any([target_words, target_cards, target_decks, target_categories])
            self.stdout.write(
                f"Target existing data: categories={target_categories}, words={target_words}, cards={target_cards}, decks={target_decks}"
            )
            if has_data and not replace_target_data:
                raise CommandError(
                    "Target user already has data. Re-run with --replace-target-data to allow overwrite."
                )

        if not apply:
            self.stdout.write(
                self.style.WARNING("DRY RUN only. Add --apply to execute cloning.")
            )
            return

        created_categories = 0
        created_words = 0
        copied_word_media = 0
        created_relations = 0
        created_decks = 0
        copied_deck_covers = 0
        created_cards = 0

        with transaction.atomic():
            if not target_exists:
                target_user = User.objects.create_user(
                    username=target_username,
                    password=target_password,
                    email=f"{target_username.lower()}@example.com",
                    preferred_language=source_user.preferred_language,
                    native_language=source_user.native_language,
                    learning_language=source_user.learning_language,
                    theme=source_user.theme,
                    mode=source_user.mode,
                    image_provider=source_user.image_provider,
                    gemini_model=source_user.gemini_model,
                    audio_provider=source_user.audio_provider,
                )
            else:
                target_user.set_password(target_password)
                target_user.save(update_fields=["password"])

                if replace_target_data:
                    Deck.objects.filter(user=target_user).delete()
                    Card.objects.filter(user=target_user).delete()
                    Word.objects.filter(user=target_user).delete()
                    Category.objects.filter(user=target_user).delete()

            # Ensure training settings for target user exist and reset counters
            target_settings, _ = UserTrainingSettings.objects.get_or_create(
                user=target_user,
                defaults={"learning_steps": [2, 10]},
            )
            target_settings.total_reviews = 0
            target_settings.successful_reviews = 0
            target_settings.last_calibration_at = 0
            target_settings.save(
                update_fields=[
                    "total_reviews",
                    "successful_reviews",
                    "last_calibration_at",
                    "updated_at",
                ]
            )

            # 1) Categories
            category_map: dict[int, Category] = {}
            source_categories_ordered = source_categories.select_related("parent").order_by("parent_id", "id")
            for src_cat in source_categories_ordered:
                new_parent = category_map.get(src_cat.parent_id) if src_cat.parent_id else None
                new_cat = Category.objects.create(
                    user=target_user,
                    name=src_cat.name,
                    parent=new_parent,
                    icon=src_cat.icon,
                    order=src_cat.order,
                    is_learning_active=src_cat.is_learning_active,
                )
                category_map[src_cat.id] = new_cat
                created_categories += 1

            # 2) Words + media
            word_map: dict[int, Word] = {}
            source_words_ordered = source_words.prefetch_related("categories").order_by("id")
            for src_word in source_words_ordered:
                new_word = Word(
                    user=target_user,
                    original_word=src_word.original_word,
                    translation=src_word.translation,
                    language=src_word.language,
                    card_type=src_word.card_type,
                    etymology=src_word.etymology,
                    sentences=src_word.sentences,
                    notes=src_word.notes,
                    hint_text=src_word.hint_text,
                    part_of_speech=src_word.part_of_speech,
                    stickers=src_word.stickers,
                    learning_status="new",
                )
                # Avoid auto AI generation signal during cloning
                setattr(new_word, "_skip_etymology_generation", True)
                new_word.save()

                image_name = _copy_filefield(src_word.image_file, "images")
                audio_name = _copy_filefield(src_word.audio_file, "audio")
                hint_audio_name = _copy_filefield(src_word.hint_audio, "hints")
                changed_fields = []
                if image_name:
                    new_word.image_file = image_name
                    changed_fields.append("image_file")
                    copied_word_media += 1
                if audio_name:
                    new_word.audio_file = audio_name
                    changed_fields.append("audio_file")
                    copied_word_media += 1
                if hint_audio_name:
                    new_word.hint_audio = hint_audio_name
                    changed_fields.append("hint_audio")
                    copied_word_media += 1
                if changed_fields:
                    new_word.save(update_fields=changed_fields + ["updated_at"])

                mapped_categories = [
                    category_map[c.id].id
                    for c in src_word.categories.all()
                    if c.id in category_map
                ]
                if mapped_categories:
                    new_word.categories.set(mapped_categories)

                word_map[src_word.id] = new_word
                created_words += 1

            # 3) Word relations
            for src_rel in source_relations.select_related("word_from", "word_to"):
                new_from = word_map.get(src_rel.word_from_id)
                new_to = word_map.get(src_rel.word_to_id)
                if not new_from or not new_to:
                    continue
                _, rel_created = WordRelation.objects.get_or_create(
                    word_from=new_from,
                    word_to=new_to,
                    relation_type=src_rel.relation_type,
                )
                if rel_created:
                    created_relations += 1

            # 4) Decks + deck cover + m2m words
            deck_map: dict[int, Deck] = {}
            for src_deck in source_decks.prefetch_related("words").order_by("id"):
                new_deck = Deck.objects.create(
                    user=target_user,
                    name=src_deck.name,
                    target_lang=src_deck.target_lang,
                    source_lang=src_deck.source_lang,
                    is_learning_active=src_deck.is_learning_active,
                )

                cover_name = _copy_filefield(src_deck.cover, "deck_covers")
                if cover_name:
                    new_deck.cover = cover_name
                    new_deck.save(update_fields=["cover", "updated_at"])
                    copied_deck_covers += 1

                mapped_word_ids = [
                    word_map[w.id].id
                    for w in src_deck.words.all()
                    if w.id in word_map
                ]
                if mapped_word_ids:
                    new_deck.words.set(mapped_word_ids)

                deck_map[src_deck.id] = new_deck
                created_decks += 1

            # 5) Cards (reset progress for independent start)
            # Remove auto-generated cards from signals to fully mirror source card set.
            Card.objects.filter(user=target_user).delete()

            cards_to_create = []
            source_cards_iter = source_cards.select_related("word").order_by("id")
            for src_card in source_cards_iter:
                mapped_word = word_map.get(src_card.word_id)
                if not mapped_word:
                    continue
                cards_to_create.append(
                    Card(
                        user=target_user,
                        word=mapped_word,
                        card_type=src_card.card_type,
                        cloze_sentence=src_card.cloze_sentence,
                        cloze_word_index=src_card.cloze_word_index,
                        ease_factor=2.5,
                        interval=0,
                        repetitions=0,
                        lapses=0,
                        consecutive_lapses=0,
                        learning_step=0,
                        next_review=None,
                        last_review=None,
                        is_in_learning_mode=True,
                        is_auxiliary=src_card.is_auxiliary,
                        is_suspended=False,
                    )
                )

            if cards_to_create:
                Card.objects.bulk_create(cards_to_create, batch_size=500)
                created_cards = len(cards_to_create)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Clone completed successfully."))
        self.stdout.write(f"Target user id: {target_user.id}")
        self.stdout.write(f"Categories created: {created_categories}")
        self.stdout.write(f"Words created: {created_words}")
        self.stdout.write(f"Word media copied (files): {copied_word_media}")
        self.stdout.write(f"Word relations created: {created_relations}")
        self.stdout.write(f"Decks created: {created_decks}")
        self.stdout.write(f"Deck covers copied: {copied_deck_covers}")
        self.stdout.write(f"Cards created (progress reset): {created_cards}")
