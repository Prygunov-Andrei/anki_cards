#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.words.models import Word
from apps.cards.models import Deck

print("📊 Проверка типов карточек в локальной базе:")
print("")

print(f"Всего слов: {Word.objects.count()}")
print(f"  - normal: {Word.objects.filter(card_type='normal').count()}")
print(f"  - inverted: {Word.objects.filter(card_type='inverted').count()}")
print(f"  - empty: {Word.objects.filter(card_type='empty').count()}")
print(f"  - Без типа: {Word.objects.filter(card_type__isnull=True).count()}")
print("")

print(f"Слов с _empty_: {Word.objects.filter(original_word__startswith='_empty_').count()}")
print("")

print(f"Колод: {Deck.objects.count()}")
deck = Deck.objects.first()
if deck:
    print(f"\nПервая колода: '{deck.name}'")
    print(f"  source_lang: {deck.source_lang}")
    print(f"  target_lang: {deck.target_lang}")
    print(f"  Слов в колоде: {deck.words.count()}")
    
    # Проверяем инвертированные
    inverted_in_deck = deck.words.filter(language=deck.source_lang)
    print(f"\n  Слов с language={deck.source_lang} (должны быть inverted): {inverted_in_deck.count()}")
    if inverted_in_deck.exists():
        print("  Примеры:")
        for w in inverted_in_deck[:3]:
            print(f"    - {w.original_word[:40]} (lang: {w.language}, type: {w.card_type})")
    
    # Проверяем обычные
    normal_in_deck = deck.words.filter(language=deck.target_lang)
    print(f"\n  Слов с language={deck.target_lang} (должны быть normal): {normal_in_deck.count()}")
    if normal_in_deck.exists():
        print("  Примеры:")
        for w in normal_in_deck[:3]:
            print(f"    - {w.original_word[:40]} (lang: {w.language}, type: {w.card_type})")
