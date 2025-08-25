from django.contrib import admin
from .models import UserAccount, Wishlist, Cart, UserFeedback

# Register your models here.
@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "street_address", "city", "region", 'is_deleted', 'deleted_at')
    list_filter = ("user", "phone_number", "street_address", "city", "region", 'is_deleted', 'deleted_at')

    def __str__(self):
        return f"{self.user.username}' account"
    


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "added_at")
    list_filter = ("user", "product", "added_at")

    def __str__(self):
        return f"{self.user.username}'s wishliast product-{self.product.title}"
    


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "color", "size", "added_at", "quantity", "updated_at")
    list_filter = ("user", "product", "color", "size", "added_at")

    def __str__(self):
        return f"Order-{self.product.title} for {self.user.username}"



@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "email", "message", "subject", "sent_at")
    list_filter = ("user", "full_name", "email", "message", "subject", "sent_at")

    def __str__(self):
        return f"feedback from {self.full_name}"
    