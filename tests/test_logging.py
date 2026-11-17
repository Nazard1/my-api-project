"""Тести логування: потрібні записи зʼявляються, а паролів і токенів у логах немає."""

import logging

import pytest
from django.urls import reverse

from tests.conftest import USER_PASSWORD

pytestmark = pytest.mark.django_db

WRONG_PASSWORD = "Wrong-2026!"


@pytest.fixture(autouse=True)
def info_logs(caplog):
    """Ловимо INFO незалежно від LOG_LEVEL у .env."""
    for name in ("catalog", "accounts", "config"):
        caplog.set_level(logging.INFO, logger=name)
    return caplog


def test_product_created_is_logged(auth_client, user, product_payload, caplog):
    response = auth_client.post(reverse("product-list"), product_payload, format="json")

    expected = f"Product created: id={response.data['id']} by user_id={user.pk}"
    records = [r for r in caplog.records if r.name == "catalog.views"]
    assert any(
        r.levelno == logging.INFO and r.getMessage() == expected for r in records
    )


def test_unauthorized_request_is_logged(api_client, product_payload, caplog):
    api_client.post(reverse("product-list"), product_payload, format="json")

    assert any(
        r.levelno == logging.WARNING
        and "POST /api/v1/products/ -> 401 (anonymous)" in r.getMessage()
        for r in caplog.records
    )


def test_conflict_is_logged(auth_client, category, product, caplog):
    auth_client.delete(reverse("category-detail", args=[category.pk]))

    assert any(
        r.levelno == logging.WARNING and "-> 409" in r.getMessage()
        for r in caplog.records
    )


def test_login_logs_have_no_secrets(api_client, user, caplog):
    api_client.post(
        reverse("login"),
        {"username": user.username, "password": WRONG_PASSWORD},
        format="json",
    )
    response = api_client.post(
        reverse("login"),
        {"username": user.username, "password": USER_PASSWORD},
        format="json",
    )

    assert f"User logged in: username={user.username}" in caplog.text
    assert USER_PASSWORD not in caplog.text
    assert WRONG_PASSWORD not in caplog.text
    assert response.data["access"] not in caplog.text


def test_register_logs_have_no_passwords(api_client, caplog):
    password = "Okun-Lyn-2026!"
    payload = {
        "username": "fisher_petro",
        "email": "petro@example.com",
        "password": password,
        "password2": password + "x",
    }

    api_client.post(reverse("register"), payload, format="json")

    assert "invalid fields: password2" in caplog.text
    assert password not in caplog.text
