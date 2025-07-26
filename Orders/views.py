from django.shortcuts import render
from .models import OrderItem, Order, PaymentTransaction, Coupon
from users.models import UserAccount
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import OrderItemSerializer, OrderSerializer
from store.models import Product
from users.models import Cart, UserAccount
import requests
import uuid
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from admin_panel.permissions import IsStaffUser
# Create your views here.



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    user = request.user
    data = request.data

    cart_items = data.get("cart_items", [])
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    email = data.get("email", "")
    city = data.get("city", "")
    region = data.get("region", "")
    phone_number = data.get("phone_number", "")
    shipping_address = data.get("shipping_address", "")
    order_type = data.get("order_type")

    try:

        if not cart_items:
            return Response({
                "status": "error",
                "message": "Cart is empty"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            account_user = UserAccount.objects.get(user=user)
        except UserAccount.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User account not found."
            }, status=status.HTTP_404_NOT_FOUND)

        total_amount = 0
        order_items = []

        for item in cart_items:
            product_id = item["product"]["id"]
            print(product_id)
            quantity = item["quantity"]

            try:
                product = Product.objects.get(id=product_id)
                print(product)
            except Product.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": f"Product with id {product_id} not found"
                }, status=status.HTTP_404_NOT_FOUND)
            

            total_amount += product.discount_price * quantity
            order_items.append((product, quantity, product.discount_price))

        order = Order.objects.create(
            user=account_user,
            total_amount=total_amount,
            shipping_address=shipping_address,
            first_name=first_name,
            last_name=last_name,
            email=email,
            region=region,
            city=city,
            phone_number=phone_number
        )

        for product, quantity, price in order_items:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=price
            )

        reference = str(uuid.uuid4())
        order.reference = reference
        order.order_type = order_type
        order.save()

        with transaction.atomic():

            user_account = UserAccount.objects.get(user=user)

            user_cart = Cart.objects.filter(user=user_account)
            user_cart.delete()


        if order_type == "delivery":

            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "email": user.email,
                "amount": int(total_amount * 100),
                "reference": reference,
                "callback_url": "http://localhost:5173/checkout/success-payment"
            }

            try:
                paystack_res = requests.post(
                    "https://api.paystack.co/transaction/initialize",
                    json=payload,
                    headers=headers
                )
                paystack_data = paystack_res.json()
            except requests.RequestException:
                return Response({
                    "status": "error",
                    "message": "Could not connect to Paystack"
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            if not paystack_data.get("status"):
                return Response({
                    "status": "error",
                    "message": "Payment initiation failed",
                    "paystack_response": paystack_data
                }, status=status.HTTP_400_BAD_REQUEST)
            

            payment = PaymentTransaction.objects.create(reference=reference, status="pending", amount=total_amount, gateway_response=paystack_data)
            order.payment = payment
            order.save()

            return Response({
                "status": "success",
                "message": "Order created. Redirect to Paystack to complete purchase.",
                "order_id": order.id,
                "reference": reference,
                "payment_link": paystack_data["data"]["authorization_url"]
            }, status=status.HTTP_201_CREATED)
        
        else:
            return Response({
                "status": "success",
                "message": "Order created. You'll be contacted soon",
                "order_id": order.id,
                "reference": reference,
                "payment_link": "http://localhost:5173/me/profile"
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    reference = request.data.get("reference")

    try:

        if not reference:
            return Response({
                "status": "error", 
                "message": "Reference is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        }

        try:
            response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
            data = response.json()
        except requests.RequestException:
            return Response({
                "status": "error", 
                "message": "Could not connect to Paystack"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not data.get("status"):
            return Response({
                "status": "error",
                "message": "Payment verification failed"
            }, status=status.HTTP_400_BAD_REQUEST)

        payment_data = data["data"]
        amount_paid = payment_data["amount"] / 100  
        status_paid = payment_data["status"]

        try:
            payment = PaymentTransaction.objects.get(reference=reference)
        except PaymentTransaction.DoesNotExist:
            return Response({
                "status": "error", 
                "message": "Payment record not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if status_paid == "success":
            payment.status = "success"
            payment.paystack_amount = amount_paid
            payment.paid_at = timezone.now()
            payment.save()

            order = Order.objects.get(reference=reference)
            order.status = "paid"
            order.payment = payment
            order.save()

            return Response({
                "status": "success", 
                "message": "Payment verified and order updated"
            }, status=status.HTTP_201_CREATED)
        else:
            payment.status = "pending"
            payment.save()
            return Response({
                "status": "error", 
                "can_pay_again": True,
                "message": "Payment was not successful"
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pay_via_reference(request):
    reference = request.data.get("reference")

    try:

        user = request.user

        try:
            order = Order.objects.get(reference=reference)
        except Order.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Order reference not found"
            }, status=status.HTTP_404_NOT_FOUND)    

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        new_reference = str(uuid.uuid4())

        payload = {
            "email": user.email,
            "amount": int(order.total_amount * 100),
            "reference": new_reference,
            "callback_url": "http://localhost:5173/checkout/success-payment"
        }

        try:
            paystack_res = requests.post(
                "https://api.paystack.co/transaction/initialize",
                json=payload,
                headers=headers
            )
            paystack_data = paystack_res.json()
        except requests.RequestException:
            return Response({
                "status": "error",
                "message": "Could not connect to Paystack"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not paystack_data.get("status"):
            return Response({
                "status": "error",
                "message": "Payment initiation failed",
                "paystack_response": paystack_data
            }, status=status.HTTP_400_BAD_REQUEST)


        try:
            payment = PaymentTransaction.objects.get(reference=reference)
            payment.reference = new_reference
            payment.save()

        except PaymentTransaction.DoesNotExist:
            payment = PaymentTransaction.objects.create(reference=new_reference, status="pending", amount=order.total_amount, gateway_response=paystack_data)
            order.payment = payment
            order.save() 
            

        order.reference = new_reference
        order.save()

        return Response({
            "status": "success",
            "message": "Order created. Redirect to Paystack to complete payment.",
            "order_id": order.id,
            "reference": reference,
            "payment_link": paystack_data["data"]["authorization_url"]
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order_by_reference(request, reference):
    try:

        try:
            order = Order.objects.get(reference=reference, user__user=request.user)
            order_reference = order.order_id
            return Response({
                "status":"success",
                "message": "ok",
                "order_id": order_reference,
            }, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({
                "error": "error",
                "message": "Order not found"
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_orders(request):
    try:

        try:

            account_user = UserAccount.objects.get(user=request.user)
        except UserAccount.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User account not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        orders = Order.objects.filter(user=account_user).order_by('-created_at')

        orders_serializer = OrderSerializer(orders, many=True)

        return Response({
            "status":"success",
            "message":"ok",
            "orders": orders_serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



@api_view(["GET"])
@permission_classes([IsStaffUser])
def get_all_orders(request):
    try:

        orders = Order.objects.all().order_by('-created_at')

        orders_serializer = OrderSerializer(orders, many=True)

        return Response({
            "status":"success",
            "message":"ok",
            "orders": orders_serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)