from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Return 422 for validation errors instead of DRF's default 400."""
    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, ValidationError):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    return response
