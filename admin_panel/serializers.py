from rest_framework import serializers
from Orders.models import Coupon



class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'
        read_only_fields = [fields]
