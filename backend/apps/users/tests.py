"""
Tests for users app
"""
import pytest
from django.contrib.auth import get_user_model
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
