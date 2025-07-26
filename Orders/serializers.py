from rest_framework import serializers
from .models import Order, OrderItem, PaymentTransaction, Coupon
from store.serializers import ProductSerializer
from users.serializers import UserAccountSerializer


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_value']
        read_only_fields = fields


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price_at_purchase']
        read_only_fields = ['id', 'created_at', 'price_at_purchase']



class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ['amount', 'status', 'paid_at']



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentTransactionSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            'order_id', 'status', 'order_type', 'total_amount',
            'first_name', 'last_name', 'email', 'region', 'city',
            'phone_number', 'shipping_address', 'created_at',
            'updated_at', 'items', 'coupon', 'payment', 'reference'
        )
        read_only_fields = ['id', 'created_at', 'updated_at', 'reference']
