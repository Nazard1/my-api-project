"""Тести CRUD категорій і брендів (спільні сценарії, параметризовані на обидва ресурси)."""

import pytest
from django.urls import reverse
from rest_framework import status

from catalog.models import Brand, Category

pytestmark = pytest.mark.django_db

RESOURCES = [
    pytest.param(
        ("category-list", "category-detail", Category, "Категорію"),
        id="categories",
    ),
    pytest.param(
        ("brand-list", "brand-detail", Brand, "Бренд"),
        id="brands",
    ),
]


@pytest.fixture(params=RESOURCES)
def resource(request):
    list_name, detail_name, model, label = request.param
    return {
        "list_url": reverse(list_name),
        "detail_url": lambda pk: reverse(detail_name, args=[pk]),
        "model": model,
        "label": label,
    }


@pytest.fixture
def obj(resource, category, brand):
    """Існуючий обʼєкт поточного ресурсу (категорія або бренд)."""
    return category if resource["model"] is Category else brand


def test_list_without_token(api_client, resource, obj):
    response = api_client.get(resource["list_url"])

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [obj.pk]


def test_create_with_token(auth_client, resource):
    response = auth_client.post(resource["list_url"], {"name": "Нове"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert resource["model"].objects.filter(name="Нове").exists()


def test_create_without_token(api_client, resource):
    response = api_client.post(resource["list_url"], {"name": "Нове"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not resource["model"].objects.exists()


def test_create_duplicate_name(auth_client, resource, obj):
    response = auth_client.post(resource["list_url"], {"name": obj.name}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data["error"]["details"]
    assert resource["model"].objects.count() == 1


def test_detail(api_client, resource, obj):
    response = api_client.get(resource["detail_url"](obj.pk))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == obj.name


def test_detail_not_found(api_client, resource):
    response = api_client.get(resource["detail_url"](999))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"]["message"] == (
        f"{resource['label']} з id=999 не знайдено."
    )
    assert response.data["error"]["details"] == {}


def test_patch(auth_client, resource, obj):
    response = auth_client.patch(
        resource["detail_url"](obj.pk), {"description": "Оновлено"}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    obj.refresh_from_db()
    assert obj.description == "Оновлено"


def test_patch_empty_name(auth_client, resource, obj):
    old_name = obj.name

    response = auth_client.patch(
        resource["detail_url"](obj.pk), {"name": ""}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data["error"]["details"]
    obj.refresh_from_db()
    assert obj.name == old_name


def test_delete_without_products(auth_client, resource, obj):
    response = auth_client.delete(resource["detail_url"](obj.pk))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not resource["model"].objects.filter(pk=obj.pk).exists()


def test_delete_with_products(auth_client, resource, obj, product):
    response = auth_client.delete(resource["detail_url"](obj.pk))

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["error"]["status"] == 409
    assert "товарів: 1" in response.data["error"]["message"]
    assert resource["model"].objects.filter(pk=obj.pk).exists()


def test_delete_without_token(api_client, resource, obj):
    response = api_client.delete(resource["detail_url"](obj.pk))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert resource["model"].objects.filter(pk=obj.pk).exists()


def test_delete_not_found(auth_client, resource):
    response = auth_client.delete(resource["detail_url"](999))

    assert response.status_code == status.HTTP_404_NOT_FOUND
