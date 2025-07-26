from django.contrib import admin
from .models import Product, Category, ProductImages

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'product_image', 'not_available', 'category', 'price', 'size', 'color', 'discount_price', 'stock', 'created_at', 'updated_at')
    search_fields = ('id', 'description', 'category', 'price', 'not_available', 'discount_price', 'size', 'color', 'stock', 'created_at', 'updated_at')
    list_filter = ('id', 'title', 'description', 'product_image', 'not_available', 'category', 'price', 'discount_price', 'stock', 'created_at', 'updated_at')

    def __str__(self):
        return f"{self.title}"



@admin.register(ProductImages)
class ProductImagesAdmin(admin.ModelAdmin):
    list_display = ("product", "image", "uploaded_at")
    search_fields = ("product", "uploaded_at")
    list_filter = ("product", "uploaded_at")

    def __str__(self):
        return f"image for product({self.product})"
    
    

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "description")
    search_fields = ("name", "slug", "description")
    list_filter = ("name", "slug")

    def __str__(self):
        return f""