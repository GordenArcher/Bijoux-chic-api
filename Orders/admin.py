from django.contrib import admin
from .models import Order, OrderItem, Coupon, PaymentTransaction

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "order_id",  "status", "total_amount", "coupon", "reference", "payment", "shipping_address", "created_at", "updated_at")
    search_fields = ("user", "order_id", "status", "total_amount", "coupon", "reference", "shipping_address")
    list_filter = ("user", "order_id", "status", "total_amount", "coupon", "reference", "shipping_address")

    def __str__(self):
        return f"Order #{self.id} by {self.user}"
    


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price_at_purchase", "created_at")
    search_fields = ("order", "product", "quantity", "price_at_purchase", "created_at")
    list_filter = ("order", "product", "quantity", "price_at_purchase", "created_at")

    def __str__(self):
        return f"order-item for {self.order}"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "is_active", "used")
    search_fields = ("code", "discount_type", "discount_value", "is_active", "used")
    list_filter =("code", "discount_type", "discount_value", "is_active", "used")

    def __str__(self):
        return f"Coupon code - {self.code}"
    


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("reference",  "amount", "paystack_amount", "status", "gateway_response", "paid_at", "created_at")
    search_fields = ("reference",  "amount", "status", "paid_at", "created_at")
    list_filter = ("reference",  "amount", "status", "paid_at", "created_at")
    

    def __str__(self):
        return f"payment of {self.amount} made -- trancID #{self.transaction_id}"