from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.views import exception_handler

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

    if isinstance(exc, ValidationError):
        message = "Дані не пройшли перевірку."
        details = response.data
    else:
        message = str(response.data.get("detail", "Помилка запиту."))
        details = {}

    response.data = {
        "error": {
            "status": response.status_code,
            "message": message,
            "details": details,
        }
    }
    return response