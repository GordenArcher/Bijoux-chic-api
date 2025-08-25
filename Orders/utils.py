import random
import string
from django.db.models import Q
from .models import Coupon

def generate_coupon_code():
    chars = string.ascii_uppercase + string.digits
    base_code = 'bjc' + ''.join(random.choice(chars) for _ in range(10))
    code = base_code
    counter = 1
    
    while Coupon.objects.filter(Q(code=code) | Q(code__startswith=base_code + '-')).exists():
        code = f"{base_code}-{counter}"
        counter += 1
        
    return code