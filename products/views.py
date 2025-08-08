from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics


from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# ---------------- Category Views ---------------- #
class CategoryListCreateView(APIView):
    def get(self, request):
        data = cache.get('categories')
        if not data:
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)
            data = serializer.data
            cache.set('categories', data, timeout=3600)  # 1 hour cache
        return Response(data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({'detail': 'Admin only'}, status=403)
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete('categories')  # Invalidate cache
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class CategoryDetailView(APIView):
    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            serializer = CategorySerializer(category)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)

    def put(self, request, pk):
        if not request.user.is_staff:
            return Response({'detail': 'Admin only'}, status=403)
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response({'detail': 'Admin only'}, status=403)
        try:
            category = Category.objects.get(pk=pk)
            category.delete()
            return Response({'detail': 'Deleted'})
        except Category.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
        


class ProductListCreateView(APIView):
    def get(self, request):
        # Query filters
        products = Product.objects.select_related('category').all()

        category = request.GET.get('category')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        in_stock = request.GET.get('in_stock')

        if category:
            products = products.filter(category__id=category)
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if in_stock == 'true':
            products = products.filter(stock__gt=0)
        elif in_stock == 'false':
            products = products.filter(stock=0)

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10  # or use settings.PAGE_SIZE
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({'detail': 'Admin only'}, status=403)
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete('products')
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class ProductDetailView(APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.select_related('category').get(pk=pk)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)

    def put(self, request, pk):
        if not request.user.is_staff:
            return Response({'detail': 'Admin only'}, status=403)
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response({'detail': 'Admin only'}, status=403)
        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            return Response({'detail': 'Deleted'})
        except Product.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)
