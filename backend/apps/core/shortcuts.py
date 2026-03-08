"""
Common shortcuts to reduce boilerplate across views.
"""
from django.shortcuts import get_object_or_404


def get_user_object_or_404(model, user, **kwargs):
    """
    Shortcut for get_object_or_404 with user filtering.

    Replaces the common pattern:
        obj = get_object_or_404(Model, id=id, user=request.user)

    Usage:
        obj = get_user_object_or_404(Word, request.user, id=word_id)
    """
    return get_object_or_404(model, user=user, **kwargs)
