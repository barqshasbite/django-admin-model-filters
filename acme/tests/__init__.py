# coding=utf-8

"""Application tests."""

import uuid

from django.contrib.auth import get_user_model


def new_user(
    username: str = None,
    password: str = None,
    is_staff: bool = False,
    is_superuser: bool = False,
    **kwargs
):
    """Create a new user."""
    if username is None:
        username = str(uuid.uuid4())
    return get_user_model().objects.create_user(
        username=username,
        password=password,
        is_staff=is_staff,
        is_superuser=is_superuser,
        **kwargs
    )
