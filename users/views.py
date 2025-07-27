from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.admin import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib import auth
from django.contrib.auth import get_user_model
from .models import UserAccount, Cart, Wishlist, UserFeedback
from .serializers import UserAccountSerializer, CartSerializer, WishlistSerializer
from store.models import Product
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.db import transaction
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from .permissions import IsFromAllowedOrigin
from admin_panel.permissions import IsStaffUser
# Create your views here.


@ensure_csrf_cookie
@api_view(["GET"])
def get_csrf_token(request):
    csrf = get_token(request)
    return Response({"message": "CSRF cookie set.", "csrf": csrf}, status=status.HTTP_200_OK)



def send_email(user):
    html_content = render_to_string("Emails/welcome.html", {
        "user": f"{user.get_full_name()}" 
    })

    email = EmailMessage(
        subject="Thanks for Joining Bijoux Chic",
        body=html_content,
        from_email="Bijoux Chic Shop <no-reply@goriaai.com>",
        to=[user.email],
    )
    email.content_subtype = "html"
    email.send()



@api_view(['POST'])
def register(request):
    data = request.data

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    username = data.get("username")
    email = data.get("email")
    phone_number = data.get("phone_number")
    password = data.get("password")
    password2 = data.get("password2")
    
    try:

        if not all([first_name, last_name, username, email, phone_number, password]):
            return Response({
                "status": "error", 
                "message": "All fields are required"
            }, status=status.HTTP_400_BAD_REQUEST)


        if password != password2:
            return Response({
                "status": "error", 
                "message": "password does not match"
            }, status=status.HTTP_400_BAD_REQUEST)


        if User.objects.filter(email=email).exists():
            return Response({
                "status": "error", 
                "message": "Email already registered"
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({
                "status": "error", 
                "message": "Username already registered"
            }, status=status.HTTP_400_BAD_REQUEST)    
        
        if UserAccount.objects.filter(phone_number=phone_number).exists():
            return Response({
                "status": "error", 
                "message": "Phone number already registered"
            }, status=status.HTTP_400_BAD_REQUEST)
    

    
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email, password=password)

        UserAccount.objects.create(user=user, phone_number=phone_number)

        token = Token.objects.create(user=user)

        send_email(user)
        

        return Response({
            "status": "success",
            "message": "Registeration successfull",
        }, status=status.HTTP_201_CREATED)
    

    except Exception as e:
        return Response({
            "status": "error", 
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    try:
        if not username or not password:
            return Response({
                "status": "error",
                "message": "All fields are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

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
                secure=True,        
                httponly=True,
                samesite='None',     
                path='/',
            )

            response.set_cookie(
                key="isLoggedIn",
                value=True,
                max_age=60*60*24*7,  
                secure=True,        
                httponly=True,
                samesite='None',     
                path='/',
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




@api_view(["GET"])
@permission_classes([IsAuthenticated])
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



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user(request):
    try:
        user = request.user

        user_account = UserAccount.objects.get(user=user)

        account_serializer = UserAccountSerializer(user_account)

        return Response({
            "status":"success",
            "message":"retrieved",
            "data": account_serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:

        Token.objects.filter(user=request.user).delete()

        auth.logout(request)

        res = Response({
            "status":"success",
            "authenticated": False,
            "message":"You logged out"
        }, status=status.HTTP_200_OK)

        res.delete_cookie(
            key="access_token",
            path="/",
        )

        res.delete_cookie(
            key="isLoggedIn",
            path="/",
        )

        
        return res
        

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_cart(request):
    product_id = request.data.get("product_id")
    quantity = request.data.get("quantity")
    color = request.data.get("color")
    size = request.data.get("size")

    try:
        if not product_id or not quantity:
            return Response({
                "status": "error",
                "message": "Product ID and quantity are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserAccount.objects.get(user=request.user)
        except UserAccount.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User account not found."
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Product does not exist."
            }, status=status.HTTP_400_BAD_REQUEST)
 

        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': quantity, "color": color, 'size': size}
        )

        return Response({
            "status": "success",
            "message": "Product added to cart."
        }, status=status.HTTP_201_CREATED)

    
    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_cart(request):
    try:

        try:
            user = UserAccount.objects.get(user=request.user)
        except UserAccount.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User account not found."
            }, status=status.HTTP_404_NOT_FOUND)

        user_cart = Cart.objects.filter(user=user)

        cart_serializer = CartSerializer(user_cart, many=True)

        return Response({
            "status":"success",
            "message":"ok",
            "cart": cart_serializer.data
        }, status=status.HTTP_200_OK)


    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_cart(request, uuid):
    try:

        try:
            user = UserAccount.objects.get(user=request.user)
        except UserAccount.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User account not found."
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            product = Product.objects.get(id=uuid)
        except Product.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Product does not exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart = Cart.objects.filter(user=user, product=product)
        cart.delete()

        return Response({
            "status":"success",
            "message":"Product removed from cart"
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_wishlist(request):
    product_id = request.data.get("product_id")

    if not product_id:
        return Response({
            "status": "error",
            "message": "Product ID is required."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = UserAccount.objects.get(user=request.user)
    except UserAccount.DoesNotExist:
        return Response({
            "status": "error",
            "message": "User account not found."
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Product does not exist."
        }, status=status.HTTP_400_BAD_REQUEST)

    wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)

    return Response({
        "status": "success",
        "message": "Product added to wishlist." if created else "Product already in wishlist."
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_wishlist(request):
    try:

        try:
            user = UserAccount.objects.get(user=request.user)
        except UserAccount.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User account not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        
        user_wishlist = Wishlist.objects.filter(user=user)

        wishlist_serializer = WishlistSerializer(user_wishlist, many=True)

        return Response({
            "status":"success",
            "message":"ok",
            "wishlist": wishlist_serializer.data
        }, status=status.HTTP_200_OK)


    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_wishlist(request, id):

    try:

        user = UserAccount.objects.get(user=request.user)

        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Product does not exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        wishlist = Wishlist.objects.filter(user=user, product=product)
        wishlist.delete()

        return Response({
            "status":"success",
            "message":"Product removed from Wishlist"
        }, status=status.HTTP_201_CREATED)


    
    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    data = request.data
    user = request.user

    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    username = data.get('username')
    phone_number = data.get('phone_number')
    profile_image = request.FILES.get('profile_image')
    street_address = data.get('street_address')
    city = data.get('city')
    region = data.get('region')

    try:

        if email and User.objects.filter(email=email).exclude(id=user.id).exists():
            return Response({
                "status":"error",
                "message":"Email already exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if phone_number and UserAccount.objects.filter(phone_number=phone_number).exclude(user=user).exists():
            return Response({
                "status":"error",
                "message":"phone number already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

        profile, created = UserAccount.objects.get_or_create(user=user)

        with transaction.atomic():

            if first_name:
                user.first_name = first_name

            if last_name:
                user.last_name = last_name   

            if username:
                user.username = username  

            if email:
                user.email = email 


            if phone_number:
                profile.phone_number = phone_number

            if profile_image:
                profile.profile_image = profile_image

            if street_address:
                profile.street_address = street_address

            if city:
                profile.city = city

            if region:
                profile.region = region

            profile.save()  
            user.save()

            return Response({
                "status":"success",
                "message": "Profile updated successfully."
            }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
   data = request.data

   old_password = data.get("currentPassword")
   new_password = data.get("newPassword")
   new_password2 = data.get("confirmPassword")

   try:
       if not all([old_password, new_password, new_password2]):
           return Response({
               "status": "error",
               "message": "All fields are required"
           }, status=status.HTTP_400_BAD_REQUEST)

       if new_password != new_password2:
           return Response({
               "status": "error",
               "message": "New passwords do not match"
           }, status=status.HTTP_400_BAD_REQUEST)

       user = request.user

       if not user.check_password(old_password):
           return Response({
               "status": "error",
               "message": "Current password is incorrect"
           }, status=status.HTTP_400_BAD_REQUEST)

       if user.check_password(new_password):
           return Response({
               "status": "error",
               "message": "New password cannot be the same as the current password"
           }, status=status.HTTP_400_BAD_REQUEST)

       user.set_password(new_password)
       user.save()

       return Response({
           "status": "success",
           "message": f"Password has been changed successful"
       }, status=status.HTTP_200_OK)

   except Exception as e:
       return Response({
           "status": "error",
           "message": "Unable to change password. Please try again."
       }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  




@api_view(["POST"])
@permission_classes([IsFromAllowedOrigin])
def user_feedback(request):
    data = request.data

    full_name = data.get("full_name")
    email = data.get("email")
    message = data.get("message")
    subject = data.get("subject")

    try:

        if not all([full_name, email, message]):
            return Response({
                "status":"error",
                "message":"All fields are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        

        UserFeedback.objects.create(full_name=full_name, message=message, email=email, subject=subject)

        return Response({
            "status":"success",
            "message":"recieved"
        }, status=status.HTTP_201_CREATED)


    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"            
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    try:

        user_account = UserAccount.objects.all()

        account_serializer = UserAccountSerializer(user_account, many=True)

        return Response({
            "status":"success",
            "message":"retrieved",
            "users": account_serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsStaffUser, IsFromAllowedOrigin])
def make_user_staff(request):
    email = request.data.get('email')

    try:

        if not email:
            return Response({
                "status":"error",
                "message": "Email is required"
                },status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.is_staff:
                return Response({
                "status":"error",
                "message": f"{email} is already staff"
                },status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "status":"error",
                "message": f"User with {email} not found"
                },status=status.HTTP_404_NOT_FOUND)
                
        user.is_staff = True
        user.save()
        return Response({
            "status":"error",
            "message": f"{email} has been granted staff status"
            },status=status.HTTP_200_OK)
    

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)