"""Тести реєстрації, входу й оновлення JWT: /api/v1/auth/."""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from config.exceptions import MSG_INVALID_CREDENTIALS, MSG_INVALID_TOKEN
from tests.conftest import USER_PASSWORD

pytestmark = pytest.mark.django_db

REGISTER_URL = reverse("register")
LOGIN_URL = reverse("login")
REFRESH_URL = reverse("token-refresh")

NEW_PASSWORD = "Okun-Lyn-2026!"


@pytest.fixture
def register_payload():
    return {
        "username": "fisher_petro",
        "first_name": "Петро",
        "last_name": "Карась",
        "email": "petro@example.com",
        "password": NEW_PASSWORD,
        "password2": NEW_PASSWORD,
    }


def test_register(api_client, register_payload):
    response = api_client.post(REGISTER_URL, register_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert set(response.data) == {"id", "username", "first_name", "last_name", "email"}
    user = User.objects.get(username="fisher_petro")
    assert user.password != NEW_PASSWORD
    assert user.check_password(NEW_PASSWORD)
    assert not user.is_staff
    assert not user.is_superuser


def test_register_ignores_fake_token(bad_token_client, register_payload):
    response = bad_token_client.post(REGISTER_URL, register_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED


def test_register_passwords_mismatch(api_client, register_payload):
    register_payload["password2"] = "Inshyi-2026!"

    response = api_client.post(REGISTER_URL, register_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"]["details"]["password2"] == ["Паролі не збігаються."]
    assert not User.objects.filter(username="fisher_petro").exists()


@pytest.mark.parametrize(
    "password",
    [
        pytest.param("12345678", id="numeric"),
        pytest.param("password", id="common"),
        pytest.param("fisher_petro1", id="like-username"),
    ],
)
def test_register_weak_password(api_client, register_payload, password):
    register_payload["password"] = password
    register_payload["password2"] = password

    response = api_client.post(REGISTER_URL, register_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data["error"]["details"]
    assert not User.objects.filter(username="fisher_petro").exists()


def test_register_username_taken(api_client, register_payload, user):
    register_payload["username"] = user.username

    response = api_client.post(REGISTER_URL, register_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"]["details"]["username"] == [
        "Користувач із таким імʼям уже існує."
    ]


def test_register_invalid_email(api_client, register_payload):
    register_payload["email"] = "not-an-email"

    response = api_client.post(REGISTER_URL, register_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data["error"]["details"]


def test_login(api_client, user):
    response = api_client.post(
        LOGIN_URL,
        {"username": user.username, "password": USER_PASSWORD},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["access"]
    assert response.data["refresh"]


def test_login_wrong_password(api_client, user):
    response = api_client.post(
        LOGIN_URL,
        {"username": user.username, "password": "Wrong-2026!"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"]["message"] == MSG_INVALID_CREDENTIALS
    assert response.data["error"]["details"] == {}


def test_login_without_password(api_client, user):
    response = api_client.post(LOGIN_URL, {"username": user.username}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data["error"]["details"]


def test_refresh(api_client, user):
    login = api_client.post(
        LOGIN_URL,
        {"username": user.username, "password": USER_PASSWORD},
        format="json",
    )

    response = api_client.post(
        REFRESH_URL, {"refresh": login.data["refresh"]}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["access"]


def test_refresh_invalid_token(api_client):
    response = api_client.post(REFRESH_URL, {"refresh": "not.a.token"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"]["message"] == MSG_INVALID_TOKEN


def test_register_login_create_category(api_client, register_payload):
    api_client.post(REGISTER_URL, register_payload, format="json")
    login = api_client.post(
        LOGIN_URL,
        {"username": "fisher_petro", "password": NEW_PASSWORD},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    response = api_client.post(
        reverse("category-list"), {"name": "Приманки"}, format="json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Приманки"
