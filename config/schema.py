from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers

from .exceptions import (
    MSG_INVALID_CREDENTIALS,
    MSG_INVALID_TOKEN,
    MSG_NOT_AUTHENTICATED,
)

class ErrorBodySerializer(serializers.Serializer):
    status = serializers.IntegerField(help_text="HTTP-статус відповіді.")
    message = serializers.CharField(help_text="Зрозуміле людині пояснення помилки.")
    details = serializers.DictField(
        help_text=(
            "Помилки по полях (лише для 400): імʼя поля → список повідомлень. "
            "Для інших статусів — порожній обʼєкт."
        ),
    )


class ErrorSerializer(serializers.Serializer):

    error = ErrorBodySerializer()


def _error_example(name, status, message, details=None):
    return OpenApiExample(
        name,
        value={
            "error": {"status": status, "message": message, "details": details or {}}
        },
        response_only=True,
        status_codes=[str(status)],
    )


def validation_error(example_details):
    return OpenApiResponse(
        ErrorSerializer,
        description="Дані не пройшли перевірку.",
        examples=[
            _error_example(
                "Помилка валідації", 400, "Дані не пройшли перевірку.", example_details
            )
        ],
    )


UNAUTHORIZED = OpenApiResponse(
    ErrorSerializer,
    description="Немає access-токена або він недійсний чи прострочений.",
    examples=[
        _error_example("Немає токена", 401, MSG_NOT_AUTHENTICATED),
        _error_example("Недійсний токен", 401, MSG_INVALID_TOKEN),
    ],
)

INVALID_CREDENTIALS = OpenApiResponse(
    ErrorSerializer,
    description="Невірне імʼя користувача або пароль.",
    examples=[_error_example("Невірні дані входу", 401, MSG_INVALID_CREDENTIALS)],
)

INVALID_REFRESH = OpenApiResponse(
    ErrorSerializer,
    description="Refresh-токен недійсний або прострочений.",
    examples=[_error_example("Недійсний refresh", 401, MSG_INVALID_TOKEN)],
)


def not_found(label):
    return OpenApiResponse(
        ErrorSerializer,
        description=f"{label} з таким id не існує.",
        examples=[_error_example("Не знайдено", 404, f"{label} з id=999 не знайдено.")],
    )


def conflict(message):
    return OpenApiResponse(
        ErrorSerializer,
        description="Обʼєкт не можна видалити, бо до нього привʼязані товари.",
        examples=[_error_example("Є повʼязані товари", 409, message)],
    )