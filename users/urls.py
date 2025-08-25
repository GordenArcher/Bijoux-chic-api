from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.register),
    path("login/", views.login),
    path("me/logout/", views.logout),
    path("is_authenticated/", views.check_authentication),
    path("me/", views.get_user),
    path("all_users/", views.get_all_users),
    path("me/update/", views.update_user_profile),
    path("me/change_password/", views.change_password),
    path("cart/", views.get_user_cart),
    path("cart/add/", views.save_cart),
    path("cart/remove/<uuid:uuid>/", views.delete_cart),
    path("wishlist/", views.get_user_wishlist),
    path("wishlist/add/", views.save_wishlist),
    path("wishlist/remove/<uuid:id>/", views.delete_wishlist),
    path("feedback/", views.user_feedback),
    # path("csrf/", views.get_csrf_token),
    path('make_admin/', views.make_user_staff),
    path('get_feedback/', views.get_feedback),
    path("delete_account/", views.delete_user_account)
]
