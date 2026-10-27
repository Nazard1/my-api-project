from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.exceptions import Conflict, get_object_or_404_api

from .models import Brand, Category
from .serializers import BrandSerializer, CategorySerializer


class BrandListView(APIView):
    def get(self, request):
        brands = Brand.objects.all()
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BrandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BrandDetailView(APIView):
    def get(self, request, pk):
        brand = get_object_or_404_api(Brand, pk, "Бренд")
        serializer = BrandSerializer(brand)
        return Response(serializer.data)

    def patch(self, request, pk):
        brand = get_object_or_404_api(Brand, pk, "Бренд")
        serializer = BrandSerializer(brand, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

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
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryDetailView(APIView):
    def get(self, request, pk):
        category = get_object_or_404_api(Category, pk, "Категорію")
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def patch(self, request, pk):
        category = get_object_or_404_api(Category, pk, "Категорію")
        serializer = CategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

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
        return Response(status=status.HTTP_204_NO_CONTENT)
