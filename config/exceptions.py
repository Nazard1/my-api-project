from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken

MSG_NOT_AUTHENTICATED = (
    "Потрібна авторизація. Передайте access-токен у заголовку "
    "Authorization: Bearer <access>."
)
MSG_INVALID_TOKEN = (
    "Токен недійсний або прострочений. Оновіть access-токен або увійдіть знову."
)
MSG_INVALID_CREDENTIALS = "Невірне імʼя користувача або пароль."
MSG_PERMISSION_DENIED = "У вас немає прав для виконання цієї дії."


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Дію неможливо виконати через конфлікт із поточними даними."
    default_code = "conflict"


def get_object_or_404_api(model, pk, label):
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        raise NotFound(f"{label} з id={pk} не знайдено.") from None


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = {}
    if isinstance(exc, ValidationError):
        message = "Дані не пройшли перевірку."
        details = response.data
    elif isinstance(exc, NotAuthenticated):
        message = MSG_NOT_AUTHENTICATED
    elif isinstance(exc, InvalidToken):
        # simplejwt кладе в detail англійський словник (detail, code, messages),
        # тому замінюємо його власним повідомленням.
        message = MSG_INVALID_TOKEN
    elif isinstance(exc, AuthenticationFailed):
        # Код no_active_account дає логін із невірним імʼям чи паролем.
        if exc.get_codes() == "no_active_account":
            message = MSG_INVALID_CREDENTIALS
        else:
            message = MSG_INVALID_TOKEN
    elif isinstance(exc, PermissionDenied):
        message = MSG_PERMISSION_DENIED
    else:
        message = str(response.data.get("detail", "Помилка запиту."))

    response.data = {
        "error": {
            "status": response.status_code,
            "message": message,
            "details": details,
        }
    }
    return response
