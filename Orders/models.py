from django.db import models
from django.contrib.auth.models import User
import uuid
import random
from datetime import datetime
# Create your models here.


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=(('percent', 'Percent'), ('amount', 'Amount')))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.code

class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    reference = models.CharField(max_length=100, unique=True)
    amount = models.PositiveIntegerField()
    paystack_amount = models.PositiveIntegerField(help_text="Amount in Kobo", null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    gateway_response = models.TextField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} - {self.status}"



class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    ORDER_TYPE = [
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
    ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    order_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    user = models.ForeignKey("users.UserAccount", on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE, default='delivery')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, related_name="payments", null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    first_name = models.TextField(blank=True, null=True)
    last_name = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    region = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    phone_number = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    reference = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_order_id(self):
        date_str = datetime.now().strftime("%Y%m%d")
        prefix = f"BiC-{date_str}-{self.user.id}"
        while True:
            rand = random.randint(10000, 99999)
            order_id = f"{prefix}-{rand}"
            if not Order.objects.filter(order_id=order_id).exists():
                return order_id
            

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_order_id()
        super().save(*args, **kwargs)
        

    def __str__(self):
        return f"Order #{self.id} by {self.user}"
    


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey("store.Product", on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product} in Order #{self.order.id}"