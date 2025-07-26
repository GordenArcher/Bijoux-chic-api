from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='user_info')
    phone_number = models.CharField(null=True, blank=True, max_length=15)
    profile_image = models.FileField(upload_to='media/profile_image', blank=True, null=True)
    street_address = models.CharField(blank=True, null=True, max_length=10000)
    city = models.CharField(blank=True, null=True, max_length=1000)
    region = models.CharField(blank=True, null=True, max_length=1000)

    def __str__(self):
        return f"{self.user.username}'s account info"


class Wishlist(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']



class Cart(models.Model):
    user =  models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f"cart saved for {self.user}"    




class UserFeedback(models.Model):
    user =  models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='feedback', blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=1000, blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"feedback from {self.full_name}"
