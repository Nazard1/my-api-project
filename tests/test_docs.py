"""Тести документації API: OpenAPI-схема, Swagger UI і ReDoc."""

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


@pytest.fixture
def schema(api_client):
    response = api_client.get(reverse("schema"), {"format": "json"})
    assert response.status_code == status.HTTP_200_OK
    return response.json()


def test_schema_has_catalog_and_auth_paths(schema):
    paths = schema["paths"]

    assert {"get", "post"} <= set(paths["/api/v1/products/"])
    assert {"get", "patch", "delete"} <= set(paths["/api/v1/products/{id}/"])
    assert "post" in paths["/api/v1/auth/login/"]


def test_schema_has_jwt_security_scheme(schema):
    assert "jwtAuth" in schema["components"]["securitySchemes"]


def test_schema_documents_category_conflict(schema):
    delete = schema["paths"]["/api/v1/categories/{id}/"]["delete"]

    assert "409" in delete["responses"]


@pytest.mark.parametrize("url_name", ["swagger-ui", "redoc"])
def test_docs_pages(api_client, url_name):
    response = api_client.get(reverse(url_name))

    assert response.status_code == status.HTTP_200_OK
