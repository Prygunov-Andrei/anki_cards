"""
Модели для сервера синхронизации Anki
"""
from django.db import models
from django.conf import settings
import uuid


class AnkiSyncUser(models.Model):
    """
    Модель для хранения данных синхронизации Anki пользователя
    Каждый пользователь имеет свою SQLite базу Anki на сервере
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='anki_sync',
        verbose_name='Пользователь'
    )
    # Путь к SQLite базе данных Anki пользователя
    collection_path = models.CharField(
        max_length=500,
        verbose_name='Путь к базе данных коллекции'
    )
    # Хост ID для синхронизации (уникальный идентификатор хоста)
    host_key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Ключ хоста'
    )
    # Время последней синхронизации
    last_sync_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время последней синхронизации'
    )
    # Версия клиента
    client_version = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Версия клиента'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Синхронизация Anki'
        verbose_name_plural = 'Синхронизации Anki'
    
    def __str__(self):
        return f"Anki Sync: {self.user.username}"


class AnkiSyncMedia(models.Model):
    """
    Модель для хранения медиафайлов синхронизации
    """
    sync_user = models.ForeignKey(
        AnkiSyncUser,
        on_delete=models.CASCADE,
        related_name='media_files',
        verbose_name='Пользователь синхронизации'
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name='Имя файла'
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name='Путь к файлу'
    )
    file_size = models.IntegerField(
        verbose_name='Размер файла'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Медиафайл синхронизации'
        verbose_name_plural = 'Медиафайлы синхронизации'
        unique_together = [['sync_user', 'file_name']]
    
    def __str__(self):
        return f"{self.file_name} ({self.sync_user.user.username})"
