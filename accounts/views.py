import logging

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from config.schema import INVALID_CREDENTIALS, INVALID_REFRESH, validation_error

from .serializers import RegisterSerializer

logger = logging.getLogger(__name__)


@extend_schema(tags=["Авторизація"])
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Реєстрація",
        description="Створює звичайного користувача. Токен не потрібен. "
        "Пароль перевіряється стандартними валідаторами Django "
        "(мінімум 8 символів, не надто простий, не лише цифри, не схожий на "
        "імʼя чи email). Паролі у відповіді не повертаються.",
        request=RegisterSerializer,
        examples=[
            OpenApiExample(
                "Новий користувач",
                value={
                    "username": "fisher_ivan",
                    "first_name": "Іван",
                    "last_name": "Коваль",
                    "email": "ivan@example.com",
                    "password": "Karas-2026!",
                    "password2": "Karas-2026!",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Створений користувач",
                value={
                    "id": 2,
                    "username": "fisher_ivan",
                    "first_name": "Іван",
                    "last_name": "Коваль",
                    "email": "ivan@example.com",
                },
                response_only=True,
            ),
        ],
        responses={
            201: RegisterSerializer,
            400: validation_error({"password2": ["Паролі не збігаються."]}),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("User registered: id=%s username=%s", user.pk, user.username)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Авторизація"],
    summary="Вхід (отримати JWT)",
    description="Повертає пару токенів: `access` (5 хвилин) для заголовка "
    "`Authorization: Bearer <access>` і `refresh` (1 день) для оновлення access.",
    examples=[
        OpenApiExample(
            "Дані входу",
            value={"username": "fisher_ivan", "password": "Karas-2026!"},
            request_only=True,
        ),
        OpenApiExample(
            "Токени",
            value={
                "refresh": "eyJhbGciOiJIUzI1NiIs...",
                "access": "eyJhbGciOiJIUzI1NiIs...",
            },
            response_only=True,
        ),
    ],
    responses={
        200: inline_serializer(
            "TokenPair",
            {"refresh": serializers.CharField(), "access": serializers.CharField()},
        ),
        400: validation_error({"password": ["Це поле обов'язкове."]}),
        401: INVALID_CREDENTIALS,
    },
)
class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        logger.info("User logged in: username=%s", request.data.get("username"))
        return response


@extend_schema(
    tags=["Авторизація"],
    summary="Оновити access-токен",
    description="Приймає `refresh` і повертає новий `access`.",
    examples=[
        OpenApiExample(
            "Refresh-токен",
            value={"refresh": "eyJhbGciOiJIUzI1NiIs..."},
            request_only=True,
        ),
        OpenApiExample(
            "Новий access",
            value={"access": "eyJhbGciOiJIUzI1NiIs..."},
            response_only=True,
        ),
    ],
    responses={
        200: inline_serializer("AccessToken", {"access": serializers.CharField()}),
        400: validation_error({"refresh": ["Це поле обов'язкове."]}),
        401: INVALID_REFRESH,
    },
)
class RefreshView(TokenRefreshView):
    pass