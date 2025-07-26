from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserAccount, Wishlist, Cart
from store.serializers import ProductSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email")



class UserAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserAccount
        fields = ['id', 'user', 'phone_number', 'profile_image', 'street_address', 'city', 'region']



class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product']



class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity', 'color', 'size', 'added_at', 'updated_at']
