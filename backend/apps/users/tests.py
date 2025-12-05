"""
Tests for users app
"""
import pytest
import os
import tempfile
from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Тесты для модели User"""

    def test_user_creation(self):
        """Тест создания пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.is_active is True
        assert user.is_staff is False
        assert user.preferred_language == 'pt'  # Значение по умолчанию

    def test_superuser_creation(self):
        """Тест создания суперпользователя"""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        assert superuser.is_superuser is True
        assert superuser.is_staff is True

    def test_user_preferred_language(self):
        """Тест установки предпочитаемого языка"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            preferred_language='de'
        )
        assert user.preferred_language == 'de'


@pytest.mark.django_db
class TestUserAPI:
    """Тесты для API пользователей"""

    def test_user_registration(self):
        """Тест регистрации пользователя"""
        client = APIClient()
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'preferred_language': 'pt'
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert response.data['username'] == 'newuser'

    def test_user_registration_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        client = APIClient()
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'differentpassword',
            'preferred_language': 'pt'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_login(self):
        """Тест входа пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data

    def test_user_login_wrong_password(self):
        """Тест входа с неверным паролем"""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_profile(self):
        """Тест получения профиля"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/user/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'

    def test_update_profile(self):
        """Тест обновления профиля"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            preferred_language='pt'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/user/profile/', {
            'preferred_language': 'de'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['preferred_language'] == 'de'
        user.refresh_from_db()
        assert user.preferred_language == 'de'


@pytest.mark.django_db
class TestUserProfileExtension:
    """Тесты для расширения модели User (Этап 5)"""

    def test_user_model_has_new_fields(self):
        """Проверка наличия всех новых полей в модели User"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Проверяем наличие полей
        assert hasattr(user, 'first_name')
        assert hasattr(user, 'last_name')
        assert hasattr(user, 'avatar')
        assert hasattr(user, 'native_language')
        assert hasattr(user, 'learning_language')
        assert hasattr(user, 'theme')

    def test_user_creation_with_all_fields(self):
        """Создание пользователя со всеми новыми полями"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Иван',
            last_name='Иванов',
            native_language='ru',
            learning_language='pt',
            theme='dark'
        )
        assert user.first_name == 'Иван'
        assert user.last_name == 'Иванов'
        assert user.native_language == 'ru'
        assert user.learning_language == 'pt'
        assert user.theme == 'dark'

    def test_user_default_values(self):
        """Проверка значений по умолчанию"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.native_language == 'ru'
        assert user.learning_language == 'pt'
        assert user.theme == 'light'

    def test_native_language_choices(self):
        """Проверка валидных значений для native_language"""
        valid_choices = ['ru', 'en', 'pt', 'de']
        for choice in valid_choices:
            user = User.objects.create_user(
                username=f'testuser_{choice}',
                email=f'test_{choice}@example.com',
                password='testpass123',
                native_language=choice
            )
            assert user.native_language == choice

    def test_learning_language_choices(self):
        """Проверка валидных значений для learning_language"""
        valid_choices = ['pt', 'de']
        for choice in valid_choices:
            user = User.objects.create_user(
                username=f'testuser_{choice}',
                email=f'test_{choice}@example.com',
                password='testpass123',
                learning_language=choice
            )
            assert user.learning_language == choice

    def test_theme_choices(self):
        """Проверка валидных значений для theme"""
        valid_choices = ['light', 'dark']
        for choice in valid_choices:
            user = User.objects.create_user(
                username=f'testuser_{choice}',
                email=f'test_{choice}@example.com',
                password='testpass123',
                theme=choice
            )
            assert user.theme == choice


@pytest.mark.django_db
class TestAvatarUpload:
    """Тесты для загрузки аватара"""

    def create_test_image(self, format='JPEG', size=(100, 100)):
        """Создает тестовое изображение"""
        img = Image.new('RGB', size, color='red')
        img_bytes = BytesIO()
        # Сохраняем с явным указанием формата
        if format == 'JPEG':
            img.save(img_bytes, format='JPEG', quality=95)
        elif format == 'PNG':
            img.save(img_bytes, format='PNG')
        elif format == 'WEBP':
            img.save(img_bytes, format='WEBP')
        else:
            img.save(img_bytes, format=format)
        img_bytes.seek(0)
        # Возвращаем байты
        return img_bytes.getvalue()

    def test_avatar_upload_valid_image(self):
        """Загрузка валидного изображения"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Создаем тестовое изображение используя временный файл
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(tmp_file.name, format='JPEG')
            tmp_file.seek(0)
            
            with open(tmp_file.name, 'rb') as f:
                avatar_file = SimpleUploadedFile(
                    "test_avatar.jpg",
                    f.read(),
                    content_type="image/jpeg"
                )
            
            response = client.patch('/api/user/profile/', {
                'avatar': avatar_file
            }, format='multipart')
            
            # Удаляем временный файл
            os.unlink(tmp_file.name)
        
        # Если ошибка, выводим её для отладки
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}: {response.data}"
        user.refresh_from_db()
        assert user.avatar is not None

    def test_avatar_upload_invalid_format(self):
        """Попытка загрузить неверный формат"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Создаем текстовый файл вместо изображения
        text_file = SimpleUploadedFile(
            "test.txt",
            b"not an image",
            content_type="text/plain"
        )
        
        response = client.patch('/api/user/profile/', {
            'avatar': text_file
        }, format='multipart')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'avatar' in response.data

    def test_avatar_upload_too_large(self):
        """Попытка загрузить файл больше 5MB"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Создаем большое изображение (больше 5MB)
        large_img = Image.new('RGB', (2000, 2000), color='red')
        img_bytes = BytesIO()
        large_img.save(img_bytes, format='JPEG', quality=100)
        img_bytes.seek(0)
        
        # Увеличиваем размер до больше 5MB
        large_data = img_bytes.read() + b'0' * (6 * 1024 * 1024)
        large_file = SimpleUploadedFile(
            "large_avatar.jpg",
            large_data,
            content_type="image/jpeg"
        )
        
        response = client.patch('/api/user/profile/', {
            'avatar': large_file
        }, format='multipart')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'avatar' in response.data

    def test_avatar_deletion(self):
        """Удаление аватара"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Сначала загружаем аватар
        img_data = self.create_test_image('JPEG')
        avatar_file = SimpleUploadedFile(
            "test_avatar.jpg",
            img_data,
            content_type="image/jpeg"
        )
        user.avatar = avatar_file
        user.save()
        
        # Теперь удаляем (используем пустую строку вместо None для multipart)
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/user/profile/', {
            'avatar': ''
        })
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.avatar is None or user.avatar == ''


@pytest.mark.django_db
class TestUserProfileAPI:
    """Тесты для API профиля пользователя (Этап 5)"""

    def test_get_profile_returns_all_fields(self):
        """GET /api/user/profile/ возвращает все поля включая новые"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Иван',
            last_name='Иванов',
            native_language='ru',
            learning_language='pt',
            theme='dark'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/user/profile/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'first_name' in response.data
        assert 'last_name' in response.data
        assert 'native_language' in response.data
        assert 'learning_language' in response.data
        assert 'theme' in response.data
        assert response.data['first_name'] == 'Иван'
        assert response.data['last_name'] == 'Иванов'
        assert response.data['native_language'] == 'ru'
        assert response.data['learning_language'] == 'pt'
        assert response.data['theme'] == 'dark'

    def test_get_profile_requires_authentication(self):
        """GET без токена возвращает 401 или 403"""
        client = APIClient()
        response = client.get('/api/user/profile/')
        # DRF может возвращать 403 вместо 401 для неавторизованных запросов
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_update_first_name(self):
        """PATCH обновляет first_name"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/user/profile/', {
            'first_name': 'Петр'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Петр'
        user.refresh_from_db()
        assert user.first_name == 'Петр'

    def test_update_last_name(self):
        """PATCH обновляет last_name"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/user/profile/', {
            'last_name': 'Петров'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['last_name'] == 'Петров'
        user.refresh_from_db()
        assert user.last_name == 'Петров'

    def test_update_native_language(self):
        """PATCH обновляет native_language"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/user/profile/', {
            'native_language': 'en'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['native_language'] == 'en'
        user.refresh_from_db()
        assert user.native_language == 'en'

    def test_update_learning_language(self):
        """PATCH обновляет learning_language"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/user/profile/', {
            'learning_language': 'de'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['learning_language'] == 'de'
        user.refresh_from_db()
        assert user.learning_language == 'de'

    def test_update_theme(self):
        """PATCH обновляет theme"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.patch('/api/user/profile/', {
            'theme': 'dark'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['theme'] == 'dark'
        user.refresh_from_db()
        assert user.theme == 'dark'

    def test_update_avatar_multipart(self):
        """PATCH с multipart/form-data загружает аватар"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Создаем тестовое изображение используя временный файл
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(tmp_file.name, format='JPEG')
            tmp_file.seek(0)
            
            with open(tmp_file.name, 'rb') as f:
                avatar_file = SimpleUploadedFile(
                    "avatar.jpg",
                    f.read(),
                    content_type="image/jpeg"
                )
            
            response = client.patch('/api/user/profile/', {
                'avatar': avatar_file
            }, format='multipart')
            
            # Удаляем временный файл
            os.unlink(tmp_file.name)
        
        # Если ошибка, выводим её для отладки
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}: {response.data}"
        user.refresh_from_db()
        assert user.avatar is not None

    def test_partial_update(self):
        """Частичное обновление (только одно поле)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Иван',
            native_language='ru'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Обновляем только theme, остальные поля не должны измениться
        response = client.patch('/api/user/profile/', {
            'theme': 'dark'
        })
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.theme == 'dark'
        assert user.first_name == 'Иван'  # Не изменилось
        assert user.native_language == 'ru'  # Не изменилось

    def test_update_invalid_language(self):
        """Попытка установить невалидное значение языка"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Пытаемся установить невалидное значение для native_language
        response = client.patch('/api/user/profile/', {
            'native_language': 'invalid'
        })
        
        # Django должен вернуть ошибку валидации
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_invalid_theme(self):
        """Попытка установить невалидное значение темы"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Пытаемся установить невалидное значение для theme
        response = client.patch('/api/user/profile/', {
            'theme': 'invalid'
        })
        
        # Django должен вернуть ошибку валидации
        assert response.status_code == status.HTTP_400_BAD_REQUEST
