from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.admin import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from rest_framework import status
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from .permissions import IsStaffUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from store.models import Product, Category
from Orders.models import Coupon, PaymentTransaction, Order
from django.utils import timezone

# Create your views here.

@api_view(['POST'])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        if not email or not password:
            return Response({
                "status": "error",
                "message": "All fields are required"
            }, status=status.HTTP_400_BAD_REQUEST)


        user = authenticate(request, email=email, password=password)

        if not user:
            try:
                user = get_user_model().objects.get(email=email)
                if user.check_password(password):
                    auth_login(request, user)
                else:
                    user = None
            except get_user_model().DoesNotExist:
                user = None

        if user is None or not user.is_staff:
            return Response({
                "status":"error",
                "message": "Unauthorized Access"
            }, status=status.HTTP_403_FORBIDDEN)        


        if user:
            Token.objects.filter(user=user).delete()

            token, _ = Token.objects.get_or_create(user=user)

            response = Response({
                "status": "success",
                "auth": True,
                "message": "Login successful",
            }, status=status.HTTP_201_CREATED)

            response.set_cookie(
                key="access_token",
                value=str(token.key),
                max_age=60*60*24*7,  
                secure=False,    
                httponly=True,
                samesite='Lax',     
                path='/',
            )

            response.set_cookie(
                key="isLoggedIn",
                value=True,
                max_age=60*60*24*7,  
                secure=False,        
                httponly=True,
                samesite='Lax',     
                path='/',
            )

            response.set_cookie(
                "csrftoken", get_token(request),
                httponly=False,
                secure=False, 
                samesite="Lax"
            )

            return response

        else:
            return Response({
                "status": "error",
                "message": "Invalid credentials"
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# endpoint for checking if user is a staff
@api_view(["GET"])
@permission_classes([IsStaffUser])
def check_authentication(request):
    try:
         
        return Response({
            "status":"success",
            "message":"authenticated",
            "auth": True   
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)       




@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_summary(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    paid_orders = Order.objects.filter(status='paid').count()
    
    total_revenue = Order.objects.filter(status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        status='paid',
        created_at__gte=thirty_days_ago
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lt=10).count()
    
    total_customers = User.objects.count()
    new_customers = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).count()
    
    return Response({
        'orders': {
            'total': total_orders,
            'pending': pending_orders,
            'paid': paid_orders,
        },
        'revenue': {
            'total': float(total_revenue),
            'last_30_days': float(monthly_revenue),
        },
        'products': {
            'total': total_products,
            'low_stock': low_stock_products,
        },
        'customers': {
            'total': total_customers,
            'new': new_customers,
        }
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def sales_over_time(request):
    days = int(request.query_params.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    date_series = [start_date + timedelta(days=i) for i in range(days + 1)]
    

    sales_data = Order.objects.filter(
        status='paid',
        created_at__date__range=[start_date, end_date]
    ).values('created_at__date').annotate(
        total_sales=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('created_at__date')
    

    sales_by_day = {item['created_at__date'].strftime('%Y-%m-%d'): {
        'amount': float(item['total_sales']),
        'orders': item['order_count']
    } for item in sales_data}
    

    formatted_data = []
    for date in date_series:
        date_str = date.strftime('%Y-%m-%d')
        formatted_data.append({
            'date': date_str,
            'amount': sales_by_day.get(date_str, {'amount': 0})['amount'],
            'orders': sales_by_day.get(date_str, {'orders': 0})['orders']
        })
    
    return Response(formatted_data)



@api_view(['GET'])
@permission_classes([IsAdminUser])
def payment_insights(request):
    total_payments = PaymentTransaction.objects.count()
    successful_payments = PaymentTransaction.objects.filter(status='success').count()
    success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
    
    failed_payments = PaymentTransaction.objects.filter(
        status='failed',
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')[:5]
    
    return Response({
        'success_rate': round(success_rate, 2),
        'recent_failures': [
            {
                'id': payment.id,
                'reference': payment.reference,
                'amount': payment.amount,
                'date': payment.created_at,
            } for payment in failed_payments
        ]
    })



@api_view(['GET'])
@permission_classes([IsAdminUser])
def category_metrics(request):
    categories = Category.objects.annotate(
        product_count=Count('category'),
        total_sold=Sum('category__orderitem__quantity'),
        total_revenue=Sum('category__orderitem__price_at_purchase')
    ).order_by('-total_revenue')
    
    return Response([
        {
            'id': category.id,
            'name': category.name,
            'products': category.product_count,
            'sold': category.total_sold or 0,
            'revenue': float(category.total_revenue or 0)
        } for category in categories
    ])



@api_view(['GET'])
@permission_classes([IsAdminUser])
def active_alerts(request):
    low_stock = Product.objects.filter(stock__lt=5).values(
        'id', 'title', 'stock'
    )[:5]
    
    # Expiring coupons
    # expiring_coupons = Coupon.objects.filter(
    #     expiry_date__lte=timezone.now() + timedelta(days=3),
    #     is_active=True
    # )
    
    pending_orders = Order.objects.filter(
        status='pending',
        created_at__lte=timezone.now() - timedelta(hours=24)
    ).count()
    
    return Response({
        'low_stock': list(low_stock),
        'pending_orders_24h': pending_orders,
        # 'expiring_coupons': expiring_coupons.count()
    })