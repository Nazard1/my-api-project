"""Спільні фікстури для тестів API «Клювання»."""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalog.models import Brand, Category, Product

USER_PASSWORD = "Karas-2026!"


@pytest.fixture
def api_client():
    """Анонімний клієнт без токена."""
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="fisher_ivan",
        email="ivan@example.com",
        password=USER_PASSWORD,
    )


@pytest.fixture
def auth_client(user):
    """Клієнт зі справжнім access-токеном у заголовку Authorization."""
    client = APIClient()
    access = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


@pytest.fixture
def bad_token_client():
    """Клієнт із підробленим токеном."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer not.a.real.token")
    return client


@pytest.fixture
def category(db):
    return Category.objects.create(name="Вудилища", description="Спінінги й фідери")


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="Shimano", country="Японія")


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        name="Спінінг Shimano Catana EX 2.40 м",
        description="Тест 10–30 г",
        price=Decimal("2450.00"),
        stock=7,
        category=category,
        brand=brand,
    )


@pytest.fixture
def product_payload(category, brand):
    """Коректні дані для створення товару."""
    return {
        "name": "Котушка Shimano Sienna 2500",
        "description": "Передній фрикціон",
        "price": "1299.00",
        "stock": 4,
        "category": category.pk,
        "brand": brand.pk,
    }
