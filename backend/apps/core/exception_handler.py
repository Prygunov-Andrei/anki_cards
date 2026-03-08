"""
Custom DRF exception handler.

Ensures all API errors return a consistent JSON format:
{"error": "message"} for single errors.
"""
import logging

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps DRF's default handler.

    Ensures consistent error format and logs server errors.
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        # If response.data is a dict with 'detail', normalize to 'error'
        if isinstance(response.data, dict) and 'detail' in response.data:
            response.data = {'error': str(response.data['detail'])}

    if response is not None and response.status_code >= 500:
        view = context.get('view', None)
        logger.error(
            "Server error in %s: %s",
            view.__class__.__name__ if view else 'unknown',
            exc,
            exc_info=True,
        )

    return response
