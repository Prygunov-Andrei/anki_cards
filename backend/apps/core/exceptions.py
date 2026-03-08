"""
Custom exceptions for the project.

These exceptions map to specific HTTP status codes and are handled
by the custom exception handler in exception_handler.py.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class InsufficientTokensError(APIException):
    """Raised when user doesn't have enough tokens for an operation."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Недостаточно токенов для выполнения операции.'
    default_code = 'insufficient_tokens'


class LLMError(APIException):
    """Raised when an LLM API call fails."""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Ошибка при обращении к AI-сервису.'
    default_code = 'llm_error'


class OwnershipError(APIException):
    """Raised when user tries to access a resource they don't own."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Объект не найден или не принадлежит пользователю.'
    default_code = 'ownership_error'
