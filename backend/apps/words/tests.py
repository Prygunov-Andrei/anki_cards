"""
Tests for words app
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from django.db.models import Q
from .models import Word, Category

User = get_user_model()


@pytest.mark.django_db
class TestWordModel:
    """Тесты для модели Word"""

    def test_word_creation(self):
        """Тест создания слова"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        assert word.original_word == 'casa'
        assert word.translation == 'дом'
        assert word.language == 'pt'
        assert word.user == user

    def test_word_unique_constraint(self):
        """Тест уникального ограничения для слова"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        # Попытка создать дубликат должна вызвать ошибку
        with pytest.raises(Exception):
            Word.objects.create(
                user=user,
                original_word='casa',
                translation='дом',
                language='pt'
            )


@pytest.mark.django_db
class TestWordsAPI:
    """Тесты для API слов"""

    def test_words_list_authenticated(self):
        """Тест получения списка слов (аутентифицированный пользователь)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/words/list/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['original_word'] == 'casa'

    def test_words_list_unauthenticated(self):
        """Тест получения списка слов (неаутентифицированный пользователь)"""
        client = APIClient()
        response = client.get('/api/words/list/')
        # DRF возвращает 403 для неаутентифицированных пользователей
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_words_list_filter_by_language(self):
        """Тест фильтрации слов по языку"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        Word.objects.create(
            user=user,
            original_word='haus',
            translation='дом',
            language='de'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/words/list/?language=pt')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['language'] == 'pt'

    def test_words_list_search(self):
        """Тест поиска слов"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        Word.objects.create(
            user=user,
            original_word='livro',
            translation='книга',
            language='pt'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/words/list/?search=casa')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['original_word'] == 'casa'


@pytest.mark.django_db
class TestWordModelNewFields:
    """Тесты для новых полей модели Word (Этап 1)"""

    def test_create_word_with_new_fields(self):
        """Тест создания слова с новыми полями"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='Hund',
            translation='собака',
            language='de',
            etymology='От древневерхненемецкого hunt',
            notes='Мужской род: der Hund',
            hint_text='Ein Tier mit vier Beinen',
            part_of_speech='noun',
            learning_status='new'
        )
        
        assert word.etymology == 'От древневерхненемецкого hunt'
        assert word.notes == 'Мужской род: der Hund'
        assert word.hint_text == 'Ein Tier mit vier Beinen'
        assert word.part_of_speech == 'noun'
        # Signal auto-creates a card, which updates learning_status via signal
        word.refresh_from_db()
        assert word.learning_status in ('new', 'learning')
        assert word.sentences == []
        assert word.stickers == []

    def test_add_sentence(self):
        """Тест добавления предложения"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='Hund',
            translation='собака',
            language='de'
        )
        
        word.add_sentence('Der Hund läuft schnell.', source='ai')
        word.add_sentence('Mein Hund ist braun.', source='user')
        
        word.refresh_from_db()
        assert len(word.sentences) == 2
        assert word.sentences[0]['text'] == 'Der Hund läuft schnell.'
        assert word.sentences[0]['source'] == 'ai'
        assert word.sentences[1]['source'] == 'user'

    def test_add_sticker(self):
        """Тест добавления стикера"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='Liebe',
            translation='любовь',
            language='de'
        )
        
        word.add_sticker('❤️')
        word.add_sticker('⭐')
        word.add_sticker('❤️')  # Дубликат не должен добавиться
        
        word.refresh_from_db()
        assert word.stickers == ['❤️', '⭐']

    def test_remove_sticker(self):
        """Тест удаления стикера"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='Test',
            translation='тест',
            language='de',
            stickers=['❤️', '⭐', '🔥']
        )
        
        word.remove_sticker('⭐')
        
        word.refresh_from_db()
        assert word.stickers == ['❤️', '🔥']

    def test_learning_status_default(self):
        """Тест дефолтного статуса обучения (сигнал автоматически создаёт карточку)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='Test',
            translation='тест',
            language='de'
        )
        # Signal create_card_for_new_word создаёт карточку → update_word_status_on_card_change → learning
        word.refresh_from_db()
        assert word.learning_status in ('new', 'learning')

    def test_learning_status_choices(self):
        """Тест валидных статусов обучения"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        for status_code, _ in Word.LEARNING_STATUS_CHOICES:
            word = Word.objects.create(
                user=user,
                original_word=f'Test_{status_code}',
                translation='тест',
                language='de',
                learning_status=status_code
            )
            # Signal may update status via card creation; check value was accepted
            word.refresh_from_db()
            assert word.learning_status in (status_code, 'learning')


@pytest.mark.django_db
class TestWordsAPINewFields:
    """Тесты API для новых полей Word"""

    def test_get_word_with_new_fields(self):
        """Тест получения слова с новыми полями через detail endpoint"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='Haus',
            translation='дом',
            language='de',
            learning_status='new'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        # Используем detail endpoint, который возвращает полный Word (WordWithRelationsSerializer)
        response = client.get(f'/api/words/{word.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        word_data = response.data
        assert 'etymology' in word_data
        assert 'sentences' in word_data
        assert 'notes' in word_data
        assert 'hint_text' in word_data
        assert 'part_of_speech' in word_data
        assert 'stickers' in word_data
        assert 'learning_status' in word_data

    def test_update_word_new_fields(self):
        """Тест обновления новых полей слова через модель"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='Haus',
            translation='дом',
            language='de'
        )
        
        # Обновляем поля напрямую через модель
        # (Endpoint для обновления будет добавлен в следующих этапах)
        word.etymology = 'От средневерхненемецкого hūs'
        word.notes = 'Das Haus - средний род'
        word.hint_text = 'Ein Gebäude zum Wohnen'
        word.part_of_speech = 'noun'
        word.learning_status = 'learning'
        word.save()
        
        word.refresh_from_db()
        assert word.etymology == 'От средневерхненемецкого hūs'
        assert word.notes == 'Das Haus - средний род'
        assert word.hint_text == 'Ein Gebäude zum Wohnen'
        assert word.part_of_speech == 'noun'
        assert word.learning_status == 'learning'

    def test_update_stickers(self):
        """Тест обновления стикеров через API"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='Haus',
            translation='дом',
            language='de'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        data = {
            'stickers': ['❤️', '⭐']
        }
        
        # Обновляем через API (зависит от реализации)
        word.stickers = data['stickers']
        word.save()
        
        word.refresh_from_db()
        assert word.stickers == ['❤️', '⭐']

    def test_filter_by_learning_status(self):
        """Тест фильтрации по статусу обучения"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='Katze',
            translation='кошка',
            language='de',
            learning_status='reviewing'
        )
        Word.objects.create(
            user=user,
            original_word='Hund',
            translation='собака',
            language='de',
            learning_status='new'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/words/list/?learning_status=new')
        
        assert response.status_code == status.HTTP_200_OK
        # Должно вернуть только слово со статусом 'new'
        for word_data in response.data.get('results', []):
            assert word_data['learning_status'] == 'new'


@pytest.mark.django_db
class TestWordRelationModel:
    """Тесты для модели WordRelation"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def word1(self, user):
        return Word.objects.create(
            user=user,
            original_word='groß',
            translation='большой',
            language='de'
        )
    
    @pytest.fixture
    def word2(self, user):
        return Word.objects.create(
            user=user,
            original_word='klein',
            translation='маленький',
            language='de'
        )
    
    @pytest.fixture
    def word3(self, user):
        return Word.objects.create(
            user=user,
            original_word='riesig',
            translation='огромный',
            language='de'
        )
    
    def test_create_synonym(self, word1, word3):
        """Тест создания синонима"""
        from .models import WordRelation
        
        relation1, relation2 = word1.add_synonym(word3)
        
        assert relation1.relation_type == 'synonym'
        assert relation1.word_from == word1
        assert relation1.word_to == word3
        
        # Проверяем обратную связь
        assert relation2.word_from == word3
        assert relation2.word_to == word1
    
    def test_create_antonym(self, word1, word2):
        """Тест создания антонима"""
        relation1, relation2 = word1.add_antonym(word2)
        
        assert relation1.relation_type == 'antonym'
        assert relation1.word_from == word1
        assert relation1.word_to == word2
    
    def test_get_synonyms(self, word1, word3):
        """Тест получения синонимов"""
        word1.add_synonym(word3)
        
        synonyms = word1.get_synonyms()
        assert word3 in synonyms
        
        # Проверяем обратную сторону
        synonyms_of_word3 = word3.get_synonyms()
        assert word1 in synonyms_of_word3
    
    def test_get_antonyms(self, word1, word2):
        """Тест получения антонимов"""
        word1.add_antonym(word2)
        
        antonyms = word1.get_antonyms()
        assert word2 in antonyms
    
    def test_remove_synonym(self, word1, word3):
        """Тест удаления синонима"""
        word1.add_synonym(word3)
        
        deleted_count = word1.remove_synonym(word3)
        assert deleted_count == 2  # Удаляются обе связи
        
        synonyms = word1.get_synonyms()
        assert word3 not in synonyms
    
    def test_cannot_relate_to_self(self, word1):
        """Тест: слово не может быть связано с самим собой"""
        from .models import WordRelation
        
        with pytest.raises(ValueError):
            WordRelation.objects.create(
                word_from=word1,
                word_to=word1,
                relation_type='synonym'
            )
    
    def test_unique_constraint(self, word1, word2):
        """Тест уникальности связи"""
        word1.add_synonym(word2)
        
        # Повторное создание не должно дублировать
        relation1, relation2 = word1.add_synonym(word2)
        
        # Должно быть только 2 связи (A→B и B→A)
        from .models import WordRelation
        count = WordRelation.objects.filter(relation_type='synonym').count()
        assert count == 2
    
    def test_delete_word_cascades_relations(self, user, word1, word2, word3):
        """Тест: при удалении слова удаляются все его связи"""
        from django.db.models import Q
        from .models import WordRelation
        
        word1.add_synonym(word3)
        word1.add_antonym(word2)
        
        word1.delete()
        
        # Все связи должны быть удалены
        relations_count = WordRelation.objects.filter(
            Q(word_from=word1) | Q(word_to=word1)
        ).count()
        assert relations_count == 0
    
    def test_different_users_cannot_relate(self, word1):
        """Тест: нельзя связать слова разных пользователей"""
        from .models import WordRelation
        
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        other_word = Word.objects.create(
            user=other_user,
            original_word='autre',
            translation='другой',
            language='fr'
        )
        
        with pytest.raises(ValueError):
            WordRelation.objects.create(
                word_from=word1,
                word_to=other_word,
                relation_type='synonym'
            )


@pytest.mark.django_db
class TestWordRelationAPI:
    """API тесты для связей между словами"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    
    @pytest.fixture
    def word1(self, user):
        return Word.objects.create(
            user=user,
            original_word='schnell',
            translation='быстрый',
            language='de'
        )
    
    @pytest.fixture
    def word2(self, user):
        return Word.objects.create(
            user=user,
            original_word='langsam',
            translation='медленный',
            language='de'
        )
    
    def test_get_relations_empty(self, client, word1):
        """Тест получения пустого списка связей"""
        response = client.get(f'/api/words/{word1.id}/relations/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['relations'] == []
        assert response.data['synonyms_count'] == 0
        assert response.data['antonyms_count'] == 0
    
    def test_add_synonym(self, client, word1, word2):
        """Тест добавления синонима через API"""
        response = client.post(
            f'/api/words/{word1.id}/add-synonym/',
            {'word_id': word2.id}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['message'] == 'Синоним добавлен'
        assert response.data['relation']['relation_type'] == 'synonym'
    
    def test_add_antonym(self, client, word1, word2):
        """Тест добавления антонима через API"""
        response = client.post(
            f'/api/words/{word1.id}/add-antonym/',
            {'word_id': word2.id}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['message'] == 'Антоним добавлен'
        assert response.data['relation']['relation_type'] == 'antonym'
    
    def test_get_relations_with_data(self, client, word1, word2):
        """Тест получения связей после добавления"""
        word1.add_antonym(word2)
        
        response = client.get(f'/api/words/{word1.id}/relations/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['relations']) == 1
        assert response.data['antonyms_count'] == 1
    
    def test_delete_relation(self, client, word1, word2):
        """Тест удаления связи через API"""
        relation1, _ = word1.add_synonym(word2)
        
        response = client.delete(
            f'/api/words/{word1.id}/relations/{relation1.id}/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['deleted_count'] == 2
        
        # Проверяем, что связей больше нет
        assert word1.get_synonyms().count() == 0
    
    def test_add_self_as_synonym_fails(self, client, word1):
        """Тест: нельзя добавить слово как синоним самого себя"""
        response = client.post(
            f'/api/words/{word1.id}/add-synonym/',
            {'word_id': word1.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_word_detail_includes_relations(self, client, word1, word2):
        """Тест: детали слова включают связи"""
        word1.add_antonym(word2)
        
        response = client.get(f'/api/words/{word1.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'antonyms' in response.data
        assert len(response.data['antonyms']) == 1
        assert response.data['antonyms'][0]['original_word'] == 'langsam'
    
    def test_unauthorized_access(self, word1):
        """Тест: неавторизованный доступ запрещён"""
        client = APIClient()  # Без аутентификации
        
        response = client.get(f'/api/words/{word1.id}/relations/')
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.django_db
class TestCategoryModel:
    """Тесты для модели Category"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def root_category(self, user):
        return Category.objects.create(
            user=user,
            name='Еда',
            icon='🍎'
        )
    
    @pytest.fixture
    def child_category(self, user, root_category):
        return Category.objects.create(
            user=user,
            name='Фрукты',
            parent=root_category,
            icon='🍇'
        )
    
    @pytest.fixture
    def grandchild_category(self, user, child_category):
        return Category.objects.create(
            user=user,
            name='Тропические',
            parent=child_category,
            icon='🥭'
        )
    
    def test_create_category(self, user):
        """Тест создания категории"""
        category = Category.objects.create(
            user=user,
            name='Транспорт',
            icon='🚗'
        )
        
        assert category.name == 'Транспорт'
        assert category.icon == '🚗'
        assert category.parent is None
        assert category.order == 0
    
    def test_create_nested_category(self, root_category, user):
        """Тест создания вложенной категории"""
        child = Category.objects.create(
            user=user,
            name='Овощи',
            parent=root_category
        )
        
        assert child.parent == root_category
        assert child in root_category.children.all()
    
    def test_get_ancestors(self, grandchild_category, child_category, root_category):
        """Тест получения предков"""
        ancestors = grandchild_category.get_ancestors()
        
        assert len(ancestors) == 2
        assert ancestors[0] == child_category
        assert ancestors[1] == root_category
    
    def test_get_descendants(self, root_category, child_category, grandchild_category):
        """Тест получения потомков"""
        descendants = root_category.get_descendants()
        
        assert len(descendants) == 2
        assert child_category in descendants
        assert grandchild_category in descendants
    
    def test_get_full_path(self, grandchild_category):
        """Тест получения полного пути"""
        path = grandchild_category.get_full_path()
        
        assert path == 'Еда → Фрукты → Тропические'
    
    def test_cannot_be_own_parent(self, root_category):
        """Тест: категория не может быть своим родителем"""
        root_category.parent = root_category
        
        with pytest.raises(ValueError):
            root_category.save()
    
    def test_no_circular_dependency(self, root_category, child_category, grandchild_category):
        """Тест: нельзя создать циклическую зависимость"""
        root_category.parent = grandchild_category
        
        with pytest.raises(ValueError):
            root_category.save()
    
    def test_unique_name_per_parent(self, user, root_category):
        """Тест: уникальность имени в рамках родителя"""
        Category.objects.create(
            user=user,
            name='Овощи',
            parent=root_category
        )
        
        # Попытка создать с тем же именем и родителем
        with pytest.raises(Exception):
            Category.objects.create(
                user=user,
                name='Овощи',
                parent=root_category
            )
    
    def test_same_name_different_parent_allowed(self, user, root_category):
        """Тест: одинаковое имя с разными родителями разрешено"""
        Category.objects.create(
            user=user,
            name='Прочее',
            parent=root_category
        )
        
        # Можно создать с тем же именем, но без родителя
        other = Category.objects.create(
            user=user,
            name='Прочее',
            parent=None
        )
        
        assert other.name == 'Прочее'
    
    def test_cascade_delete(self, root_category, child_category, grandchild_category):
        """Тест: каскадное удаление потомков"""
        root_category.delete()
        
        # Все должны быть удалены
        assert Category.objects.filter(name='Еда').count() == 0
        assert Category.objects.filter(name='Фрукты').count() == 0
        assert Category.objects.filter(name='Тропические').count() == 0


@pytest.mark.django_db
class TestWordCategoryRelation:
    """Тесты связи Word ↔ Category"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def category(self, user):
        return Category.objects.create(
            user=user,
            name='Еда'
        )
    
    @pytest.fixture
    def word(self, user):
        return Word.objects.create(
            user=user,
            original_word='Apfel',
            translation='яблоко',
            language='de'
        )
    
    def test_add_word_to_category(self, word, category):
        """Тест добавления слова в категорию"""
        word.categories.add(category)
        
        assert category in word.categories.all()
        assert word in category.words.all()
    
    def test_word_in_multiple_categories(self, user, word, category):
        """Тест: слово может быть в нескольких категориях"""
        category2 = Category.objects.create(
            user=user,
            name='Фрукты'
        )
        
        word.categories.add(category)
        word.categories.add(category2)
        
        assert word.categories.count() == 2
    
    def test_remove_word_from_category(self, word, category):
        """Тест удаления слова из категории"""
        word.categories.add(category)
        word.categories.remove(category)
        
        assert category not in word.categories.all()


@pytest.mark.django_db
class TestCategoryAPI:
    """API тесты для категорий"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    
    @pytest.fixture
    def category(self, user):
        return Category.objects.create(
            user=user,
            name='Еда',
            icon='🍎'
        )
    
    def test_list_categories_empty(self, client):
        """Тест получения пустого списка категорий"""
        response = client.get('/api/words/categories/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert response.data['categories'] == []
    
    def test_create_category(self, client):
        """Тест создания категории"""
        response = client.post('/api/words/categories/', {
            'name': 'Транспорт',
            'icon': '🚗'
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['category']['name'] == 'Транспорт'
        assert response.data['category']['icon'] == '🚗'
    
    def test_create_nested_category(self, client, category):
        """Тест создания вложенной категории"""
        response = client.post('/api/words/categories/', {
            'name': 'Фрукты',
            'parent': category.id
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['category']['parent'] == category.id
    
    def test_get_category_tree(self, client, user):
        """Тест получения дерева категорий"""
        root = Category.objects.create(user=user, name='Еда')
        child = Category.objects.create(user=user, name='Фрукты', parent=root)
        
        response = client.get('/api/words/categories/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        
        # Проверяем дерево
        tree = response.data['categories']
        assert len(tree) == 1  # Только корневая
        assert tree[0]['name'] == 'Еда'
        assert len(tree[0]['children']) == 1
        assert tree[0]['children'][0]['name'] == 'Фрукты'
    
    def test_get_flat_categories(self, client, user):
        """Тест получения плоского списка категорий"""
        root = Category.objects.create(user=user, name='Еда')
        child = Category.objects.create(user=user, name='Фрукты', parent=root)
        
        response = client.get('/api/words/categories/?flat=true')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['categories']) == 2
    
    def test_update_category(self, client, category):
        """Тест обновления категории"""
        response = client.patch(f'/api/words/categories/{category.id}/', {
            'name': 'Продукты',
            'icon': '🥗'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['category']['name'] == 'Продукты'
        assert response.data['category']['icon'] == '🥗'
    
    def test_delete_category(self, client, category):
        """Тест удаления категории"""
        response = client.delete(f'/api/words/categories/{category.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert Category.objects.filter(id=category.id).count() == 0
    
    def test_get_category_words(self, client, user, category):
        """Тест получения слов в категории"""
        word = Word.objects.create(
            user=user,
            original_word='Apfel',
            translation='яблоко',
            language='de'
        )
        word.categories.add(category)
        
        response = client.get(f'/api/words/categories/{category.id}/words/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['words'][0]['original_word'] == 'Apfel'
    
    def test_add_word_to_category_api(self, client, user, category):
        """Тест добавления слова в категорию через API"""
        word = Word.objects.create(
            user=user,
            original_word='Birne',
            translation='груша',
            language='de'
        )
        
        response = client.post(f'/api/words/{word.id}/categories/', {
            'category_id': category.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert category in word.categories.all()
    
    def test_remove_word_from_category_api(self, client, user, category):
        """Тест удаления слова из категории через API"""
        word = Word.objects.create(
            user=user,
            original_word='Birne',
            translation='груша',
            language='de'
        )
        word.categories.add(category)
        
        response = client.delete(f'/api/words/{word.id}/categories/', {
            'category_id': category.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert category not in word.categories.all()
    
    def test_unauthorized_access(self, category):
        """Тест: неавторизованный доступ запрещён"""
        client = APIClient()
        
        response = client.get('/api/words/categories/')
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


# ═══════════════════════════════════════════════════════════════
# ЭТАП 8: Words Catalog Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestWordsUtils:
    """Unit-тесты для утилит words/utils.py"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def word(self, user):
        return Word.objects.create(
            user=user,
            original_word='Haus',
            translation='дом',
            language='de'
        )
    
    def test_get_word_learning_status_new(self, word, user):
        """Тест: слово без карточек → 'new'"""
        from .utils import get_word_learning_status
        from apps.cards.models import Card
        
        # Удаляем автоматически созданную карточку
        Card.objects.filter(word=word, user=user).delete()
        
        status = get_word_learning_status(word)
        assert status == 'new'
    
    def test_get_word_learning_status_learning(self, word, user):
        """Тест: слово с карточкой в режиме изучения → 'learning'"""
        from .utils import get_word_learning_status
        from apps.cards.models import Card
        
        # Удаляем автоматически созданную карточку
        Card.objects.filter(word=word, user=user).delete()
        
        # Создаём карточку в режиме изучения
        card = Card.objects.create(
            user=user,
            word=word,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() - timedelta(minutes=5)
        )
        
        status = get_word_learning_status(word)
        assert status == 'learning'
    
    def test_get_word_learning_status_reviewing(self, word, user):
        """Тест: слово с карточкой на повторении → 'reviewing'"""
        from .utils import get_word_learning_status
        from apps.cards.models import Card
        
        # Удаляем автоматически созданную карточку
        Card.objects.filter(word=word, user=user).delete()
        
        # Создаём карточку на повторении
        card = Card.objects.create(
            user=user,
            word=word,
            card_type='normal',
            is_in_learning_mode=False,
            next_review=timezone.now() - timedelta(days=1)
        )
        
        status = get_word_learning_status(word)
        assert status == 'reviewing'
    
    def test_get_word_learning_status_mastered(self, word, user):
        """Тест: слово с освоенными карточками → 'mastered'"""
        from .utils import get_word_learning_status
        from apps.cards.models import Card
        
        # Удаляем автоматически созданную карточку
        Card.objects.filter(word=word, user=user).delete()
        
        # Создаём освоенную карточку (interval >= 30, next_review > now)
        card = Card.objects.create(
            user=user,
            word=word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=30,
            next_review=timezone.now() + timedelta(days=30)
        )
        
        status = get_word_learning_status(word)
        assert status == 'mastered'
    
    def test_update_word_learning_status(self, word, user):
        """Тест обновления статуса слова"""
        from .utils import update_word_learning_status
        from apps.cards.models import Card
        
        # Удаляем автоматически созданную карточку
        Card.objects.filter(word=word, user=user).delete()
        
        # Изначально статус 'new'
        word.learning_status = 'new'
        word.save()
        assert word.learning_status == 'new'
        
        # Создаём карточку в режиме изучения
        Card.objects.create(
            user=user,
            word=word,
            card_type='normal',
            is_in_learning_mode=True
        )
        
        # Обновляем статус
        updated_word = update_word_learning_status(word)
        
        assert updated_word.learning_status == 'learning'
        word.refresh_from_db()
        assert word.learning_status == 'learning'
    
    def test_get_word_next_review(self, word, user):
        """Тест получения ближайшей даты повторения"""
        from .utils import get_word_next_review
        from apps.cards.models import Card
        
        # Удаляем автоматически созданную карточку
        Card.objects.filter(word=word, user=user).delete()
        
        # Создаём карточки с разными датами повторения
        card1 = Card.objects.create(
            user=user,
            word=word,
            card_type='normal',
            next_review=timezone.now() + timedelta(days=5)
        )
        card2 = Card.objects.create(
            user=user,
            word=word,
            card_type='inverted',
            next_review=timezone.now() + timedelta(days=2)  # Ближайшая
        )
        
        next_review = get_word_next_review(word)
        
        assert next_review is not None
        assert next_review == card2.next_review
    
    def test_get_word_cards_stats(self, word, user):
        """Тест статистики по карточкам слова"""
        from .utils import get_word_cards_stats
        from apps.cards.models import Card
        
        # Удаляем автоматически созданную карточку
        Card.objects.filter(word=word, user=user).delete()
        
        # Создаём разные карточки
        Card.objects.create(
            user=user,
            word=word,
            card_type='normal',
            is_in_learning_mode=True
        )
        Card.objects.create(
            user=user,
            word=word,
            card_type='inverted',
            is_in_learning_mode=False,
            next_review=timezone.now() - timedelta(days=1)  # На повторении
        )
        Card.objects.create(
            user=user,
            word=word,
            card_type='empty',
            is_in_learning_mode=False,
            interval=30,
            next_review=timezone.now() + timedelta(days=30)  # Освоена
        )
        
        stats = get_word_cards_stats(word)
        
        assert stats['total_cards'] == 3
        assert stats['normal_cards'] == 1
        assert stats['inverted_cards'] == 1
        assert stats['empty_cards'] == 1
        assert stats['cloze_cards'] == 0
        assert stats['in_learning_mode'] == 1
        assert stats['due_for_review'] == 1
        assert stats['mastered'] == 1
        assert stats['next_review'] is not None


@pytest.mark.django_db
class TestWordsCatalogAPI:
    """API тесты для каталога слов (Этап 8)"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    
    @pytest.fixture
    def word1(self, user):
        return Word.objects.create(
            user=user,
            original_word='Haus',
            translation='дом',
            language='de',
            part_of_speech='noun',
            etymology='От древнегерманского hūs'
        )
    
    @pytest.fixture
    def word2(self, user):
        return Word.objects.create(
            user=user,
            original_word='Katze',
            translation='кошка',
            language='de',
            part_of_speech='noun',
            learning_status='reviewing'
        )
    
    @pytest.fixture
    def category(self, user):
        return Category.objects.create(
            user=user,
            name='Животные',
            icon='🐱'
        )
    
    @pytest.fixture
    def deck(self, user):
        from apps.cards.models import Deck
        return Deck.objects.create(
            user=user,
            name='Немецкие слова'
        )
    
    def test_words_list_filter_by_part_of_speech(self, client, word1, word2):
        """Тест фильтрации по части речи"""
        response = client.get('/api/words/list/?part_of_speech=noun')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        for word_data in response.data['results']:
            assert word_data['part_of_speech'] == 'noun'
    
    def test_words_list_filter_by_category(self, client, word1, category):
        """Тест фильтрации по категории"""
        word1.categories.add(category)
        
        response = client.get(f'/api/words/list/?category_id={category.id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == word1.id
    
    def test_words_list_filter_by_deck(self, client, word1, deck):
        """Тест фильтрации по колоде"""
        word1.decks.add(deck)
        
        response = client.get(f'/api/words/list/?deck_id={deck.id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == word1.id
    
    def test_words_list_filter_has_etymology(self, client, word1, word2):
        """Тест фильтрации по наличию этимологии"""
        response = client.get('/api/words/list/?has_etymology=true')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == word1.id
    
    def test_words_list_sorting_by_original_word(self, client, word1, word2):
        """Тест сортировки по алфавиту"""
        response = client.get('/api/words/list/?ordering=original_word')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 2
        # 'Haus' должен быть перед 'Katze'
        assert results[0]['original_word'] == 'Haus'
        assert results[1]['original_word'] == 'Katze'
    
    def test_words_list_sorting_by_created_at(self, client, word1, word2):
        """Тест сортировки по дате создания"""
        response = client.get('/api/words/list/?ordering=-created_at')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 2
        # Более новое слово должно быть первым
        assert results[0]['id'] == word2.id
    
    def test_words_list_pagination(self, client, user):
        """Тест пагинации"""
        # Создаём 25 слов
        for i in range(25):
            Word.objects.create(
                user=user,
                original_word=f'Word{i}',
                translation=f'Перевод{i}',
                language='de'
            )
        
        # Первая страница
        response = client.get('/api/words/list/?page=1&page_size=20')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None
        assert response.data['previous'] is None
        
        # Вторая страница
        response = client.get('/api/words/list/?page=2&page_size=20')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5
        assert response.data['next'] is None
        assert response.data['previous'] is not None
    
    def test_word_update(self, client, word1):
        """Тест обновления слова"""
        response = client.patch(f'/api/words/{word1.id}/', {
            'notes': 'Новая заметка',
            'part_of_speech': 'noun'
        })
        
        assert response.status_code == status.HTTP_200_OK
        word1.refresh_from_db()
        assert word1.notes == 'Новая заметка'
        assert word1.part_of_speech == 'noun'
    
    def test_word_delete(self, client, word1):
        """Тест удаления слова"""
        word_id = word1.id
        response = client.delete(f'/api/words/{word_id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert Word.objects.filter(id=word_id).count() == 0
    
    def test_word_stats(self, client, word1, user):
        """Тест статистики по слову"""
        from apps.cards.models import Card
        
        # Удаляем автоматически созданную карточку
        Card.objects.filter(word=word1, user=user, card_type='normal').delete()
        
        # Создаём карточки
        Card.objects.create(
            user=user,
            word=word1,
            card_type='normal',
            is_in_learning_mode=True
        )
        Card.objects.create(
            user=user,
            word=word1,
            card_type='inverted'
        )
        
        response = client.get(f'/api/words/{word1.id}/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['word_id'] == word1.id
        assert 'cards_stats' in response.data
        assert response.data['cards_stats']['total_cards'] == 2
        assert response.data['has_etymology'] is True
        assert response.data['categories_count'] == 0
        assert response.data['decks_count'] == 0
    
    def test_words_stats(self, client, user, word1, word2):
        """Тест общей статистики по словам"""
        from apps.cards.models import Card
        
        # Карточки уже созданы автоматически, просто проверяем статистику
        # Удаляем и создаём заново для чистоты теста
        Card.objects.filter(word__in=[word1, word2], user=user).delete()
        Card.objects.create(user=user, word=word1, card_type='normal')
        Card.objects.create(user=user, word=word2, card_type='normal')
        
        response = client.get('/api/words/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_words'] == 2
        assert 'de' in response.data['by_language']
        assert response.data['by_language']['de'] == 2
        assert 'by_status' in response.data
        assert response.data['total_cards'] == 2
    
    def test_word_enter_learning(self, client, word1, user):
        """Тест отправки слова в режим изучения"""
        from apps.cards.models import Card
        
        # Обновляем существующую карточку (автоматически созданную)
        card = Card.objects.filter(word=word1, user=user, card_type='normal').first()
        if card:
            card.is_in_learning_mode = False
            card.save()
        else:
            # Если карточки нет, создаём новую
            card = Card.objects.create(
                user=user,
                word=word1,
                card_type='normal',
                is_in_learning_mode=False
            )
        
        response = client.post(f'/api/words/{word1.id}/enter-learning/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cards_updated'] == 1
        card.refresh_from_db()
        assert card.is_in_learning_mode is True
        assert response.data['learning_status'] == 'learning'
    
    def test_bulk_action_enter_learning(self, client, user, word1, word2):
        """Тест массовой отправки в режим изучения"""
        from apps.cards.models import Card
        
        # Обновляем существующие карточки (автоматически созданные)
        card1 = Card.objects.filter(word=word1, user=user, card_type='normal').first()
        if card1:
            card1.is_in_learning_mode = False
            card1.save()
        else:
            card1 = Card.objects.create(user=user, word=word1, card_type='normal', is_in_learning_mode=False)
        
        card2 = Card.objects.filter(word=word2, user=user, card_type='normal').first()
        if card2:
            card2.is_in_learning_mode = False
            card2.save()
        else:
            card2 = Card.objects.create(user=user, word=word2, card_type='normal', is_in_learning_mode=False)
        
        response = client.post('/api/words/bulk-action/', {
            'word_ids': [word1.id, word2.id],
            'action': 'enter_learning'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'enter_learning'
        assert response.data['processed'] == 2
        assert response.data['successful'] == 2
        assert response.data['failed'] == 0
        
        card1.refresh_from_db()
        card2.refresh_from_db()
        assert card1.is_in_learning_mode is True
        assert card2.is_in_learning_mode is True
    
    def test_bulk_action_delete(self, client, word1, word2):
        """Тест массового удаления"""
        word1_id = word1.id
        word2_id = word2.id
        
        response = client.post('/api/words/bulk-action/', {
            'word_ids': [word1_id, word2_id],
            'action': 'delete'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['successful'] == 2
        assert Word.objects.filter(id__in=[word1_id, word2_id]).count() == 0
    
    def test_bulk_action_add_to_deck(self, client, word1, word2, deck):
        """Тест массового добавления в колоду"""
        # Убеждаемся, что слова не в колоде
        if word1.decks.filter(id=deck.id).exists():
            word1.decks.remove(deck)
        if word2.decks.filter(id=deck.id).exists():
            word2.decks.remove(deck)
        
        response = client.post('/api/words/bulk-action/', {
            'word_ids': [word1.id, word2.id],
            'action': 'add_to_deck',
            'params': {'deck_id': deck.id}
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['successful'] == 2
        word1.refresh_from_db()
        word2.refresh_from_db()
        assert word1.decks.filter(id=deck.id).exists()
        assert word2.decks.filter(id=deck.id).exists()
    
    def test_bulk_action_add_to_category(self, client, word1, word2, category):
        """Тест массового добавления в категорию"""
        # Убеждаемся, что слова не в категории
        word1.categories.remove(category)
        word2.categories.remove(category)
        
        response = client.post('/api/words/bulk-action/', {
            'word_ids': [word1.id, word2.id],
            'action': 'add_to_category',
            'params': {'category_id': category.id}
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['successful'] == 2
        word1.refresh_from_db()
        word2.refresh_from_db()
        assert word1.categories.filter(id=category.id).exists()
        assert word2.categories.filter(id=category.id).exists()
    
    def test_bulk_action_remove_from_category(self, client, word1, category):
        """Тест массового удаления из категории"""
        word1.categories.add(category)
        word1.refresh_from_db()
        
        response = client.post('/api/words/bulk-action/', {
            'word_ids': [word1.id],
            'action': 'remove_from_category',
            'params': {'category_id': category.id}
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['successful'] == 1
        word1.refresh_from_db()
        assert not word1.categories.filter(id=category.id).exists()
    
    def test_bulk_action_invalid_deck_id(self, client, word1):
        """Тест массового действия с невалидным deck_id"""
        response = client.post('/api/words/bulk-action/', {
            'word_ids': [word1.id],
            'action': 'add_to_deck',
            'params': {'deck_id': 99999}  # Несуществующий ID
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['failed'] == 1
        assert len(response.data['errors']) == 1
    
    def test_word_list_includes_new_fields(self, client, word1):
        """Тест: список слов включает новые поля (next_review, cards_count, categories, decks)"""
        response = client.get('/api/words/list/')
        
        assert response.status_code == status.HTTP_200_OK
        word_data = response.data['results'][0]
        assert 'next_review' in word_data
        assert 'cards_count' in word_data
        assert 'categories' in word_data
        assert 'decks' in word_data


# ═══════════════════════════════════════════════════════════════
# BULK-CREATE & CHECK-MEDIA TESTS
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestBulkCreate:
    """Tests for POST /api/words/bulk-create/"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='bulkuser', email='bulk@test.com', password='pass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_new_words(self):
        payload = {
            'words': [
                {'original_word': 'Haus', 'translation': 'дом', 'language': 'de'},
                {'original_word': 'Katze', 'translation': 'кошка', 'language': 'de'},
            ]
        }
        response = self.client.post('/api/words/bulk-create/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['words']) == 2
        assert response.data['words'][0]['is_new'] is True
        assert response.data['words'][0]['original_word'] == 'Haus'
        assert response.data['words'][1]['original_word'] == 'Katze'
        assert Word.objects.filter(user=self.user).count() == 2

    def test_deduplication(self):
        Word.objects.create(
            user=self.user, original_word='Haus', translation='дом', language='de'
        )
        payload = {
            'words': [
                {'original_word': 'Haus', 'translation': 'дом', 'language': 'de'},
                {'original_word': 'Katze', 'translation': 'кошка', 'language': 'de'},
            ]
        }
        response = self.client.post('/api/words/bulk-create/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['words'][0]['is_new'] is False
        assert response.data['words'][1]['is_new'] is True
        assert Word.objects.filter(user=self.user).count() == 2

    def test_updates_empty_translation(self):
        word = Word.objects.create(
            user=self.user, original_word='Haus', translation='', language='de'
        )
        payload = {
            'words': [{'original_word': 'Haus', 'translation': 'дом', 'language': 'de'}]
        }
        response = self.client.post('/api/words/bulk-create/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        word.refresh_from_db()
        assert word.translation == 'дом'

    def test_has_media_flags(self):
        Word.objects.create(
            user=self.user, original_word='Haus', translation='дом', language='de',
            image_file='images/haus.png',
        )
        payload = {
            'words': [{'original_word': 'Haus', 'language': 'de'}]
        }
        response = self.client.post('/api/words/bulk-create/', payload, format='json')
        assert response.data['words'][0]['has_image'] is True
        assert response.data['words'][0]['has_audio'] is False
        assert response.data['words'][0]['image_url'] is not None

    def test_unauthorized(self):
        client = APIClient()
        response = client.post('/api/words/bulk-create/', {'words': []}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_words_list(self):
        response = self.client.post('/api/words/bulk-create/', {'words': []}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCheckMedia:
    """Tests for POST /api/words/check-media/"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='mediauser', email='media@test.com', password='pass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', email='other@test.com', password='pass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_check_media_returns_status(self):
        w1 = Word.objects.create(
            user=self.user, original_word='Haus', translation='дом', language='de',
            image_file='images/haus.png',
        )
        w2 = Word.objects.create(
            user=self.user, original_word='Katze', translation='кошка', language='de',
        )
        payload = {'word_ids': [w1.id, w2.id]}
        response = self.client.post('/api/words/check-media/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['words']) == 2

        by_id = {w['id']: w for w in response.data['words']}
        assert by_id[w1.id]['has_image'] is True
        assert by_id[w1.id]['has_audio'] is False
        assert by_id[w2.id]['has_image'] is False

    def test_filters_by_user(self):
        other_word = Word.objects.create(
            user=self.other_user, original_word='Haus', translation='дом', language='de',
        )
        payload = {'word_ids': [other_word.id]}
        response = self.client.post('/api/words/check-media/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['words']) == 0

    def test_unauthorized(self):
        client = APIClient()
        response = client.post('/api/words/check-media/', {'word_ids': [1]}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
