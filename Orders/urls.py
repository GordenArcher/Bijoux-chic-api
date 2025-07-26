from django.urls import path
from . import views

urlpatterns = [
    path("order/checkout/", views.checkout),
    path("order/checkout_via_reference/", views.pay_via_reference),
    path("order/checkout/verify/", views.verify_payment),
    path("me/orders/", views.get_user_orders),
    path("me/reference/<str:reference>/", views.get_order_by_reference),
    path("all_orders/", views.get_all_orders),
]
