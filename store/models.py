from django.db import models
import uuid
from autoslug import AutoSlugField
from django.utils.text import slugify
import random
import string

# Create your models here.

def name_plus_random(model_instance):
    name_part = ''.join([c for c in model_instance.name[:3] if c.isalpha()]).lower()
    
    random_part = ''.join(random.choices(string.ascii_lowercase, k=3))
    
    return f"{name_part}{random_part}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(
        populate_from=name_plus_random,
        unique=True,
        max_length=6
    )
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='store/category/', null=True, blank=True)

    def __str__(self):
        return self.name
    

class Product(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    product_image = models.ImageField(upload_to='store/main_product/', null=True, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='category')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    not_available = models.BooleanField(default=False)
    is_hot = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_best = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    


class ProductImages(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", blank=True, null=True)
    image = models.ImageField(upload_to='store/product/images/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"image for {self.product}"