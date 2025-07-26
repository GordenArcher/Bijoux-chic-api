from rest_framework import serializers
from .models import Product, Category, ProductImages


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ["image"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'description',
            'price',
            'discount_price',
            'product_image',
            'alt_text',
            'stock',
            'category',
            'size',
            'not_available',
            'color',
            'is_hot',
            'is_new',
            'is_best',
            'is_trending',
            'is_featured',
            'images',
        ]
