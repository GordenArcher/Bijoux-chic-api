from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Coupon, Order
from .views import STAFF_ORDERS_CACHE_KEY
from admin_panel.views import COUPONS_CACHE_KEY
from utils.cache.user_orders_cache_key import user_orders_cache_key

@receiver([post_save, post_delete], sender=Coupon)
def clear_coupon_cache(sender, instance, **kwargs):
    """
        Clear cached coupons whenever a coupon is created, updated, or deleted.
    """
    cache.delete(COUPONS_CACHE_KEY)
    print(f"🧹 Cleared cache for coupons: {COUPONS_CACHE_KEY}")


@receiver([post_save, post_delete], sender=Order)
def clear_user_orders_cache(sender, instance, **kwargs):
    """
        Clear cached orders for a user whenever an order is created, updated, or deleted.
    """
    
    if instance.user:
        cache_key = user_orders_cache_key(instance.user.id)
        cache.delete(cache_key)
    
    cache.delete(STAFF_ORDERS_CACHE_KEY)
    print(f"Cleared cache for staff orders: {STAFF_ORDERS_CACHE_KEY}")
