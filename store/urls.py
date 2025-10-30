from django.urls import path
from . import views

urlpatterns = [
    path("products/all/", views.get_products),
    path("products/admin_all/", views.get_all_products),
    path("product/<str:uuid>/", views.get_product_via_id),
    path("category/", views.get_categories),
    path("category/create/", views.create_category),
    path("category/product/", views.get_product_via_category),
    path('products/create/', views.create_product, name='create-product'),
    path('products/<uuid:product_id>/edit/', views.edit_product, name='edit-product'),
    path("products/delete/", views.delete_product),
]