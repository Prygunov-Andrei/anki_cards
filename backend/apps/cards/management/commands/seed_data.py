"""
Фабрика данных для наполнения БД тестовыми данными.

Использование:
    python manage.py seed_data
    python manage.py seed_data --decks 10 --words 15
    python manage.py seed_data --clear  # Очистить перед созданием
"""

import os
import random
from io import BytesIO
from PIL import Image
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from apps.users.models import User
from apps.words.models import Word
from apps.cards.models import Deck


# Тестовые данные
GERMAN_WORDS = [
    "der Hund", "die Katze", "das Haus", "der Baum", "die Blume",
    "der Tisch", "der Stuhl", "das Fenster", "die Tür", "das Buch",
    "der Apfel", "die Banane", "das Auto", "der Zug", "das Flugzeug",
    "der Computer", "das Telefon", "die Lampe", "der Schrank", "das Bett",
    "die Küche", "das Bad", "der Garten", "die Straße", "der Park",
    "das Restaurant", "das Café", "der Supermarkt", "die Schule", "das Krankenhaus",
    "der Arzt", "die Lehrerin", "der Student", "das Kind", "die Familie",
    "der Freund", "die Freundin", "der Bruder", "die Schwester", "die Mutter",
    "der Vater", "die Großmutter", "der Großvater", "das Baby", "der Hase",
    "die Maus", "der Vogel", "der Fisch", "die Schildkröte", "der Elefant",
    "das Pferd", "die Kuh", "das Schwein", "das Schaf", "die Ziege",
    "der Berg", "das Meer", "der Fluss", "der See", "der Wald",
    "die Sonne", "der Mond", "der Stern", "die Wolke", "der Regen",
    "der Schnee", "der Wind", "das Gewitter", "der Regenbogen", "das Eis",
    "das Feuer", "das Wasser", "die Erde", "die Luft", "der Himmel",
    "das Frühstück", "das Mittagessen", "das Abendessen", "der Kaffee", "der Tee",
    "das Brot", "die Butter", "der Käse", "die Milch", "das Ei",
    "das Fleisch", "der Fisch", "das Gemüse", "das Obst", "der Salat",
    "die Suppe", "die Pizza", "die Pasta", "der Reis", "die Kartoffel",
    "rot", "blau", "grün", "gelb", "schwarz", "weiß", "grau", "braun",
]

RUSSIAN_TRANSLATIONS = [
    "собака", "кошка", "дом", "дерево", "цветок",
    "стол", "стул", "окно", "дверь", "книга",
    "яблоко", "банан", "машина", "поезд", "самолёт",
    "компьютер", "телефон", "лампа", "шкаф", "кровать",
    "кухня", "ванная", "сад", "улица", "парк",
    "ресторан", "кафе", "супермаркет", "школа", "больница",
    "врач", "учительница", "студент", "ребёнок", "семья",
    "друг", "подруга", "брат", "сестра", "мать",
    "отец", "бабушка", "дедушка", "малыш", "заяц",
    "мышь", "птица", "рыба", "черепаха", "слон",
    "лошадь", "корова", "свинья", "овца", "коза",
    "гора", "море", "река", "озеро", "лес",
    "солнце", "луна", "звезда", "облако", "дождь",
    "снег", "ветер", "гроза", "радуга", "лёд",
    "огонь", "вода", "земля", "воздух", "небо",
    "завтрак", "обед", "ужин", "кофе", "чай",
    "хлеб", "масло", "сыр", "молоко", "яйцо",
    "мясо", "рыба", "овощи", "фрукты", "салат",
    "суп", "пицца", "паста", "рис", "картошка",
    "красный", "синий", "зелёный", "жёлтый", "чёрный", "белый", "серый", "коричневый",
]

DECK_THEMES = [
    "Животные", "Еда", "Дом", "Семья", "Природа",
    "Транспорт", "Цвета", "Погода", "Город", "Школа",
    "Работа", "Спорт", "Музыка", "Одежда", "Тело",
    "Числа", "Время", "Путешествия", "Здоровье", "Хобби",
    "Кухня", "Ванная", "Гостиная", "Спальня", "Офис",
    "Магазин", "Ресторан", "Парк", "Пляж", "Горы",
]

# Цвета для placeholder изображений
COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F8B500", "#00CED1", "#FF7F50", "#9370DB", "#20B2AA",
    "#FFB6C1", "#87CEEB", "#98FB98", "#DEB887", "#F0E68C",
]


class Command(BaseCommand):
    help = 'Наполняет базу данных тестовыми данными (колоды, слова, изображения)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--decks',
            type=int,
            default=30,
            help='Количество колод (по умолчанию: 30)'
        )
        parser.add_argument(
            '--words',
            type=int,
            default=25,
            help='Среднее количество слов в колоде (по умолчанию: 25)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед созданием'
        )

    def handle(self, *args, **options):
        num_decks = options['decks']
        avg_words = options['words']
        clear = options['clear']

        self.stdout.write(self.style.WARNING(f'🏭 Запуск фабрики данных...'))
        self.stdout.write(f'   Колод: {num_decks}')
        self.stdout.write(f'   Слов в колоде: {avg_words} (±5)')

        # Получаем или создаём пользователя
        user = self._get_or_create_user()

        if clear:
            self._clear_data(user)

        # Создаём слова
        words = self._create_words(user)
        self.stdout.write(self.style.SUCCESS(f'✅ Создано слов: {len(words)}'))

        # Создаём колоды
        decks = self._create_decks(user, words, num_decks, avg_words)
        self.stdout.write(self.style.SUCCESS(f'✅ Создано колод: {len(decks)}'))

        # Итог
        total_words_in_decks = sum(d.words.count() for d in decks)
        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Готово! Создано {len(decks)} колод с {total_words_in_decks} словами.'
        ))
        self.stdout.write(f'   Пользователь: {user.username}')

    def _get_or_create_user(self):
        """Получает или создаёт тестового пользователя"""
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f'   Создан пользователь: admin / admin123')
        return user

    def _clear_data(self, user):
        """Очищает существующие данные пользователя"""
        self.stdout.write(self.style.WARNING('🗑️  Очистка существующих данных...'))
        Deck.objects.filter(user=user).delete()
        Word.objects.filter(user=user).delete()
        self.stdout.write('   Данные очищены.')

    def _create_placeholder_image(self, color: str) -> ContentFile:
        """Создаёт однотонное placeholder изображение"""
        img = Image.new('RGB', (400, 400), color)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return ContentFile(buffer.read(), name=f'placeholder_{color.replace("#", "")}.png')

    def _create_words(self, user) -> list:
        """Создаёт тестовые слова"""
        words = []
        
        for i, (german, russian) in enumerate(zip(GERMAN_WORDS, RUSSIAN_TRANSLATIONS)):
            # Проверяем, существует ли уже такое слово
            word, created = Word.objects.get_or_create(
                user=user,
                original_word=german,
                language='de',
                defaults={
                    'translation': russian,
                }
            )
            
            # Создаём placeholder изображение если нет
            if not word.image_file:
                color = random.choice(COLORS)
                word.image_file = self._create_placeholder_image(color)
                word.save()
            
            words.append(word)
            
            if (i + 1) % 20 == 0:
                self.stdout.write(f'   Создано слов: {i + 1}...')

        return words

    def _create_decks(self, user, words: list, num_decks: int, avg_words: int) -> list:
        """Создаёт тестовые колоды"""
        decks = []
        
        for i in range(num_decks):
            theme = DECK_THEMES[i % len(DECK_THEMES)]
            deck_name = f"{theme} #{i + 1}"
            
            # Создаём колоду
            deck, created = Deck.objects.get_or_create(
                user=user,
                name=deck_name,
                defaults={
                    'target_lang': 'de',
                    'source_lang': 'ru',
                }
            )
            
            if created:
                # Создаём обложку колоды
                color = random.choice(COLORS)
                deck.cover = self._create_placeholder_image(color)
                deck.save()
                
                # Добавляем случайные слова в колоду
                num_words = random.randint(avg_words - 5, avg_words + 5)
                deck_words = random.sample(words, min(num_words, len(words)))
                deck.words.set(deck_words)
            
            decks.append(deck)
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f'   Создано колод: {i + 1}...')

        return decks

