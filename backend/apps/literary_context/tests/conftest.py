import pytest
from django.contrib.auth import get_user_model
from apps.literary_context.models import (
    LiterarySource, LiteraryText, SceneAnchor, LiteraryFragment,
    LiteraryContextSettings,
)
from apps.words.models import Word

User = get_user_model()


@pytest.fixture
def chekhov_source(db):
    return LiterarySource.objects.create(
        slug='chekhov',
        name='Chekhov Stories',
        source_language='ru',
        available_languages=['ru', 'de', 'en'],
    )


@pytest.fixture
def bible_source(db):
    return LiterarySource.objects.create(
        slug='bible',
        name='Bible',
        source_language='en',
        available_languages=['ru', 'de', 'en', 'pt'],
    )


@pytest.fixture
def hameleon_text_ru(db, chekhov_source):
    return LiteraryText.objects.create(
        source=chekhov_source,
        slug='hameleon',
        title='Hameleon',
        language='ru',
        full_text=(
            'Cherez bazarnuyu ploshchad idyot politseiskii nadziratel Ochumelov '
            'v novoi shineli i s uzelkom v ruke. Za nim shagaet ryzhii gorodovoi '
            's reshetom, dokverkhu napolnennym konfiskovannym kryzhovnikom.'
        ),
    )


@pytest.fixture
def hameleon_text_de(db, chekhov_source):
    return LiteraryText.objects.create(
        source=chekhov_source,
        slug='hameleon',
        title='Das Chamaeleon',
        language='de',
        full_text=(
            'Ueber den Marktplatz geht der Polizeiaufseher Ochumelow '
            'in einem neuen Mantel und mit einem Buendel in der Hand.'
        ),
    )


@pytest.fixture
def scene_anchor(db, chekhov_source):
    return SceneAnchor.objects.create(
        source=chekhov_source,
        text_slug='hameleon',
        fragment_index=0,
        scene_description='A town square. A police officer walks across the market.',
        characters=['Ochumelov'],
        mood='comedic',
    )


@pytest.fixture
def fragment_ru(db, scene_anchor, hameleon_text_ru):
    return LiteraryFragment.objects.create(
        anchor=scene_anchor,
        text=hameleon_text_ru,
        content=hameleon_text_ru.full_text,
        key_words=['ploshchad', 'politseiskii', 'nadziratel', 'shinel'],
    )


@pytest.fixture
def fragment_de(db, scene_anchor, hameleon_text_de):
    return LiteraryFragment.objects.create(
        anchor=scene_anchor,
        text=hameleon_text_de,
        content=hameleon_text_de.full_text,
        key_words=['Marktplatz', 'Polizeiaufseher', 'Mantel'],
    )


@pytest.fixture
def settings_obj(db):
    return LiteraryContextSettings.get()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='testuser', password='testpass123',
        learning_language='de', native_language='ru',
    )


@pytest.fixture
def word_hund(db, test_user):
    return Word.objects.create(
        user=test_user,
        original_word='Hund',
        translation='собака',
        language='de',
    )


@pytest.fixture
def word_marktplatz(db, test_user):
    return Word.objects.create(
        user=test_user,
        original_word='Marktplatz',
        translation='площадь',
        language='de',
    )


@pytest.fixture
def test_user_with_settings(db):
    """User with custom LLM settings."""
    return User.objects.create_user(
        username='customuser', password='testpass123',
        learning_language='de', native_language='ru',
        hint_generation_model='gpt-4o',
        hint_temperature=0.5,
        matching_model='gpt-4o',
        elevenlabs_voice_id='voice123',
        hint_prompt_template='Custom hint for {word}: {translation}',
    )


@pytest.fixture
def deck_with_words(db, test_user, chekhov_source, fragment_de):
    """Deck with 3 words for async job testing."""
    from apps.cards.models import Deck
    deck = Deck.objects.create(
        name='Test Deck',
        user=test_user,
        target_lang='de',
        source_lang='ru',
    )
    words = []
    for w, t in [('Marktplatz', 'площадь'), ('Mantel', 'пальто'), ('Hund', 'собака')]:
        word = Word.objects.create(
            user=test_user, original_word=w, translation=t, language='de',
        )
        deck.words.add(word)
        words.append(word)
    return deck, words
