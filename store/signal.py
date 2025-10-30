from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product

@receiver([post_save, post_delete], sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    try:
        keys_to_clear = [
            "all_public_products",
            "all_admin_products",
            f"products_in_{instance.category.name.lower()}"
        ]

        for key in keys_to_clear:
            cache.delete(key)
            print(f"🧹 Cache cleared for {key}")

    except Exception as e:
        print(f"⚠️ Error clearing cache: {e}")
