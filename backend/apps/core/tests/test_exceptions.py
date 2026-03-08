"""Tests for core exceptions and exception handler."""
import pytest
from unittest.mock import MagicMock
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError

from apps.core.exceptions import InsufficientTokensError, LLMError, OwnershipError
from apps.core.exception_handler import custom_exception_handler


class TestCustomExceptions:
    def test_insufficient_tokens_status_code(self):
        exc = InsufficientTokensError()
        assert exc.status_code == status.HTTP_402_PAYMENT_REQUIRED

    def test_insufficient_tokens_detail(self):
        exc = InsufficientTokensError('Нужно 5 токенов')
        assert str(exc.detail) == 'Нужно 5 токенов'

    def test_llm_error_status_code(self):
        exc = LLMError()
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY

    def test_ownership_error_status_code(self):
        exc = OwnershipError()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_default_messages(self):
        assert 'токенов' in str(InsufficientTokensError().detail)
        assert 'AI' in str(LLMError().detail)
        assert 'не найден' in str(OwnershipError().detail)


class TestExceptionHandler:
    def _make_context(self):
        return {
            'view': MagicMock(__class__=MagicMock(__name__='TestView')),
            'request': MagicMock(),
        }

    def test_normalizes_detail_to_error(self):
        exc = NotFound('Не найдено')
        response = custom_exception_handler(exc, self._make_context())
        assert response is not None
        assert 'error' in response.data
        assert response.data['error'] == 'Не найдено'

    def test_custom_exception_handled(self):
        exc = InsufficientTokensError('Мало токенов')
        response = custom_exception_handler(exc, self._make_context())
        assert response is not None
        assert response.status_code == 402
        assert response.data['error'] == 'Мало токенов'

    def test_validation_error_preserved(self):
        exc = ValidationError({'field': ['required']})
        response = custom_exception_handler(exc, self._make_context())
        assert response is not None
        # ValidationError has list data, not 'detail' key — should pass through
        assert response.status_code == 400

    def test_non_drf_exception_returns_none(self):
        exc = RuntimeError('boom')
        response = custom_exception_handler(exc, self._make_context())
        assert response is None
