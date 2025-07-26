from django.urls import path
from . import views

urlpatterns = [
    path("authenticate/", views.login),
    path("is_authenticated/", views.check_authentication),
    path('dashboard/summary/', views.dashboard_summary),
    path('dashboard/sales/', views.sales_over_time),
    path('dashboard/payments/', views.payment_insights),
    path('dashboard/categories/', views.category_metrics),
    path('dashboard/alerts/', views.active_alerts),
]
