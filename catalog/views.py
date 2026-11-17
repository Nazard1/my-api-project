import logging

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from config.exceptions import Conflict, get_object_or_404_api
from config.schema import UNAUTHORIZED, conflict, not_found, validation_error

from .models import Brand, Category, Product
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer

logger = logging.getLogger(__name__)

PRODUCT_EXAMPLE = OpenApiExample(
    "Товар",
    value={
        "name": "Спінінг Shimano Catana EX 2.40 м",
        "description": "Тест 10–30 г, два коліна",
        "price": "2450.00",
        "stock": 7,
        "category": 1,
        "brand": 1,
    },
    request_only=True,
)
PRODUCT_RESPONSE_EXAMPLE = OpenApiExample(
    "Товар",
    value={
        "id": 1,
        "name": "Спінінг Shimano Catana EX 2.40 м",
        "description": "Тест 10–30 г, два коліна",
        "price": "2450.00",
        "stock": 7,
        "category": 1,
        "category_name": "Вудилища",
        "brand": 1,
        "brand_name": "Shimano",
        "created_at": "2026-11-17T18:30:00Z",
    },
    response_only=True,
)
PRODUCT_PATCH_EXAMPLE = OpenApiExample(
    "Змінити ціну й залишок",
    value={"price": "2299.00", "stock": 5},
    request_only=True,
)

CATEGORY_EXAMPLE = OpenApiExample(
    "Категорія",
    value={"name": "Вудилища", "description": "Спінінги, фідери, поплавкові вудки"},
    request_only=True,
)
BRAND_EXAMPLE = OpenApiExample(
    "Бренд",
    value={"name": "Shimano", "country": "Японія", "description": "Котушки й вудилища"},
    request_only=True,
)

CATEGORY_CONFLICT = (
    "Неможливо видалити категорію «Вудилища»: до неї привʼязано товарів: 3. "
    "Спочатку видаліть ці товари або перенесіть їх в іншу категорію."
)
BRAND_CONFLICT = (
    "Неможливо видалити бренд «Shimano»: за ним закріплено товарів: 3. "
    "Спочатку видаліть ці товари або змініть їм бренд."
)


def _user(request):
    return f"user_id={request.user.pk}" if request.user.is_authenticated else "anonymous"

@extend_schema(tags=["Бренди"])
class BrandListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Список брендів",
        description="Усі бренди, упорядковані за `id`, без пагінації. Доступно всім.",
        responses={200: BrandSerializer(many=True)},
    )
    def get(self, request):
        brands = Brand.objects.all()
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Створити бренд",
        description="Потрібен access-токен. Назва бренду має бути унікальною.",
        request=BrandSerializer,
        examples=[BRAND_EXAMPLE],
        responses={
            201: BrandSerializer,
            400: validation_error({"name": ["brand з таким name вже існує."]}),
            401: UNAUTHORIZED,
        },
    )
    def post(self, request):
        serializer = BrandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        brand = serializer.save()
        logger.info("Brand created: id=%s by %s", brand.pk, _user(request))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Категорії"])
class CategoryListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Список категорій",
        description="Усі категорії, упорядковані за `id`, без пагінації. Доступно всім.",
        responses={200: CategorySerializer(many=True)},
    )
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Створити категорію",
        description="Потрібен access-токен. Назва категорії має бути унікальною.",
        request=CategorySerializer,
        examples=[CATEGORY_EXAMPLE],
        responses={
            201: CategorySerializer,
            400: validation_error({"name": ["Це поле обов'язкове."]}),
            401: UNAUTHORIZED,
        },
    )
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        logger.info("Category created: id=%s by %s", category.pk, _user(request))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Бренди"])
class BrandDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Один бренд",
        responses={200: BrandSerializer, 404: not_found("Бренд")},
    )
    def get(self, request, pk):
        brand = get_object_or_404_api(Brand, pk, "Бренд")
        serializer = BrandSerializer(brand)
        return Response(serializer.data)

    @extend_schema(
        summary="Змінити бренд",
        description="Часткове оновлення: передайте лише поля, які змінюються. "
        "Потрібен access-токен.",
        request=BrandSerializer(partial=True),
        examples=[
            OpenApiExample("Змінити країну", value={"country": "Японія"}, request_only=True)
        ],
        responses={
            200: BrandSerializer,
            400: validation_error({"name": ["Це поле не може бути порожнім."]}),
            401: UNAUTHORIZED,
            404: not_found("Бренд"),
        },
    )
    def patch(self, request, pk):
        brand = get_object_or_404_api(Brand, pk, "Бренд")
        serializer = BrandSerializer(brand, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Brand updated: id=%s by %s", brand.pk, _user(request))
        return Response(serializer.data)

    @extend_schema(
        summary="Видалити бренд",
        description="Потрібен access-токен. Бренд, за яким закріплені товари, "
        "видалити не можна — сервер поверне `409`.",
        responses={
            204: None,
            401: UNAUTHORIZED,
            404: not_found("Бренд"),
            409: conflict(BRAND_CONFLICT),
        },
    )
    def delete(self, request, pk):
        brand = get_object_or_404_api(Brand, pk, "Бренд")
        count = brand.products.count()
        if count > 0:
            raise Conflict(
                f"Неможливо видалити бренд «{brand.name}»: "
                f"за ним закріплено товарів: {count}. "
                "Спочатку видаліть ці товари або змініть їм бренд."
            )
        brand.delete()
        logger.info("Brand deleted: id=%s by %s", pk, _user(request))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Категорії"])
class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Одна категорія",
        responses={200: CategorySerializer, 404: not_found("Категорію")},
    )
    def get(self, request, pk):
        category = get_object_or_404_api(Category, pk, "Категорію")
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    @extend_schema(
        summary="Змінити категорію",
        description="Часткове оновлення: передайте лише поля, які змінюються. "
        "Потрібен access-токен.",
        request=CategorySerializer(partial=True),
        examples=[
            OpenApiExample(
                "Змінити опис",
                value={"description": "Спінінги та фідери"},
                request_only=True,
            )
        ],
        responses={
            200: CategorySerializer,
            400: validation_error({"name": ["Це поле не може бути порожнім."]}),
            401: UNAUTHORIZED,
            404: not_found("Категорію"),
        },
    )
    def patch(self, request, pk):
        category = get_object_or_404_api(Category, pk, "Категорію")
        serializer = CategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Category updated: id=%s by %s", category.pk, _user(request))
        return Response(serializer.data)

    @extend_schema(
        summary="Видалити категорію",
        description="Потрібен access-токен. Категорію, до якої привʼязані товари, "
        "видалити не можна — сервер поверне `409`.",
        responses={
            204: None,
            401: UNAUTHORIZED,
            404: not_found("Категорію"),
            409: conflict(CATEGORY_CONFLICT),
        },
    )
    def delete(self, request, pk):
        category = get_object_or_404_api(Category, pk, "Категорію")
        count = category.products.count()
        if count > 0:
            raise Conflict(
                f"Неможливо видалити категорію «{category.name}»: "
                f"до неї привʼязано товарів: {count}. "
                "Спочатку видаліть ці товари або перенесіть їх в іншу категорію."
            )
        category.delete()
        logger.info("Category deleted: id=%s by %s", pk, _user(request))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Товари"])
class ProductListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Список товарів",
        description="Усі товари, упорядковані за `id`, без пагінації. "
        "Разом з `id` категорії й бренду повертаються їхні назви. Доступно всім.",
        responses={200: ProductSerializer(many=True)},
        examples=[PRODUCT_RESPONSE_EXAMPLE],
    )
    def get(self, request):
        products = Product.objects.select_related("category", "brand")
        serializer = ProductSerializer(products, many=True)
        logger.debug("Product list requested: %s items", len(serializer.data))
        return Response(serializer.data)

    @extend_schema(
        summary="Створити товар",
        description="Потрібен access-токен. Обовʼязкові поля: `name`, `price` "
        "(не менше 0.01), `category`, `brand` (id наявних обʼєктів). "
        "`stock` — ціле число ≥ 0, за замовчуванням 0.",
        request=ProductSerializer,
        examples=[PRODUCT_EXAMPLE, PRODUCT_RESPONSE_EXAMPLE],
        responses={
            201: ProductSerializer,
            400: validation_error(
                {
                    "price": ["Переконайтесь, що значення більше або дорівнює 0.01."],
                    "category": [
                        "Недопустимий первинний ключ \"999\" - об'єкт не існує."
                    ],
                }
            ),
            401: UNAUTHORIZED,
        },
    )
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        logger.info("Product created: id=%s by %s", product.pk, _user(request))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Товари"])
class ProductDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Один товар",
        responses={200: ProductSerializer, 404: not_found("Товар")},
        examples=[PRODUCT_RESPONSE_EXAMPLE],
    )
    def get(self, request, pk):
        product = get_object_or_404_api(Product, pk, "Товар")
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    @extend_schema(
        summary="Змінити товар",
        description="Часткове оновлення: передайте лише поля, які змінюються. "
        "Потрібен access-токен.",
        request=ProductSerializer(partial=True),
        examples=[PRODUCT_PATCH_EXAMPLE, PRODUCT_RESPONSE_EXAMPLE],
        responses={
            200: ProductSerializer,
            400: validation_error(
                {"stock": ["Переконайтесь, що значення більше або дорівнює 0."]}
            ),
            401: UNAUTHORIZED,
            404: not_found("Товар"),
        },
    )
    def patch(self, request, pk):
        product = get_object_or_404_api(Product, pk, "Товар")
        serializer = ProductSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(
            "Product updated: id=%s fields=%s by %s",
            product.pk,
            sorted(serializer.validated_data),
            _user(request),
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Видалити товар",
        description="Потрібен access-токен.",
        responses={204: None, 401: UNAUTHORIZED, 404: not_found("Товар")},
    )
    def delete(self, request, pk):
        product = get_object_or_404_api(Product, pk, "Товар")
        product.delete()
        logger.info("Product deleted: id=%s by %s", pk, _user(request))
        return Response(status=status.HTTP_204_NO_CONTENT)
