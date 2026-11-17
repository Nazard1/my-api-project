"""Тести CRUD товарів: /api/v1/products/."""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalog.models import Product
from config.exceptions import MSG_INVALID_TOKEN, MSG_NOT_AUTHENTICATED

pytestmark = pytest.mark.django_db

LIST_URL = reverse("product-list")


def detail_url(pk):
    return reverse("product-detail", args=[pk])


# --- Читання ---


def test_list_without_token(api_client, product):
    response = api_client.get(LIST_URL)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    item = response.data[0]
    assert item["id"] == product.pk
    assert item["category_name"] == "Вудилища"
    assert item["brand_name"] == "Shimano"


def test_detail_without_token(api_client, product):
    response = api_client.get(detail_url(product.pk))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == product.name
    assert response.data["price"] == "2450.00"
    assert response.data["category_name"] == "Вудилища"
    assert response.data["brand_name"] == "Shimano"


def test_detail_not_found(api_client):
    response = api_client.get(detail_url(999))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"]["status"] == 404
    assert response.data["error"]["message"] == "Товар з id=999 не знайдено."
    assert response.data["error"]["details"] == {}


# --- Створення ---


def test_create_with_token(auth_client, product_payload):
    response = auth_client.post(LIST_URL, product_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    product = Product.objects.get(pk=response.data["id"])
    assert product.name == product_payload["name"]
    assert product.price == Decimal("1299.00")
    assert product.stock == 4
    assert response.data["category_name"] == "Вудилища"


def test_create_stock_defaults_to_zero(auth_client, product_payload):
    del product_payload["stock"]

    response = auth_client.post(LIST_URL, product_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["stock"] == 0
    assert Product.objects.get(pk=response.data["id"]).stock == 0


def test_create_without_token(api_client, product_payload):
    response = api_client.post(LIST_URL, product_payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"]["message"] == MSG_NOT_AUTHENTICATED
    assert response.data["error"]["details"] == {}
    assert not Product.objects.exists()


def test_create_with_fake_token(bad_token_client, product_payload):
    response = bad_token_client.post(LIST_URL, product_payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"]["message"] == MSG_INVALID_TOKEN
    assert not Product.objects.exists()


def test_create_with_token_of_deleted_user(product_payload):
    ghost = User.objects.create_user(username="ghost", password="Ghost-2026!")
    access = RefreshToken.for_user(ghost).access_token
    ghost.delete()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = client.post(LIST_URL, product_payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"]["message"] == MSG_INVALID_TOKEN
    assert not Product.objects.exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("price", "0", id="price-zero"),
        pytest.param("price", "-10", id="price-negative"),
        pytest.param("price", "abc", id="price-not-number"),
        pytest.param("stock", -1, id="stock-negative"),
        pytest.param("name", "", id="name-empty"),
        pytest.param("category", 999, id="category-missing"),
        pytest.param("brand", 999, id="brand-missing"),
    ],
)
def test_create_invalid_field(auth_client, product_payload, field, value):
    product_payload[field] = value

    response = auth_client.post(LIST_URL, product_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"]["status"] == 400
    assert field in response.data["error"]["details"]
    assert not Product.objects.exists()


def test_create_empty_body(auth_client):
    response = auth_client.post(LIST_URL, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    details = response.data["error"]["details"]
    assert {"name", "price", "category", "brand"} <= set(details)


# --- Оновлення ---


def test_patch_changes_only_given_fields(auth_client, product):
    response = auth_client.patch(
        detail_url(product.pk), {"price": "2299.00"}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    product.refresh_from_db()
    assert product.price == Decimal("2299.00")
    assert product.name == "Спінінг Shimano Catana EX 2.40 м"
    assert product.stock == 7


def test_patch_without_token(api_client, product):
    response = api_client.patch(detail_url(product.pk), {"stock": 1}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    product.refresh_from_db()
    assert product.stock == 7


def test_patch_invalid(auth_client, product):
    response = auth_client.patch(detail_url(product.pk), {"stock": -5}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "stock" in response.data["error"]["details"]
    product.refresh_from_db()
    assert product.stock == 7


def test_patch_not_found(auth_client):
    response = auth_client.patch(detail_url(999), {"stock": 1}, format="json")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_put_not_allowed(auth_client, product, product_payload):
    response = auth_client.put(detail_url(product.pk), product_payload, format="json")

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert response.data["error"]["status"] == 405


# --- Видалення ---


def test_delete_with_token(auth_client, product):
    response = auth_client.delete(detail_url(product.pk))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Product.objects.filter(pk=product.pk).exists()


def test_delete_without_token(api_client, product):
    response = api_client.delete(detail_url(product.pk))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Product.objects.filter(pk=product.pk).exists()


def test_delete_not_found(auth_client):
    response = auth_client.delete(detail_url(999))

    assert response.status_code == status.HTTP_404_NOT_FOUND
