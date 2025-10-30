from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.contrib import auth
from .models import UserAccount, Cart, Wishlist, UserFeedback
from .serializers import UserAccountSerializer, CartSerializer, WishlistSerializer, UserFeedbackSerializer
from store.models import Product
from django.db import transaction
from admin_panel.permissions import IsStaffUser
from handlers.tasks.sendMail import send_email
from utils.cookies.setCookies import set_jwt_cookies
from utils.cookies.deleteCookies import remove_jwt_cookies
# Create your views here.


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
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

        welcome_message = send_email.delay(user)

        return Response({
            "status": "success",
            "message": "Email was not sucessfull but account registration was successful" if not welcome_message else "Registeration successfull",
        }, status=status.HTTP_201_CREATED)
    

    except Exception as e:
        return Response({
            "status": "error", 
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
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

            try:
                user_account = UserAccount.objects.get(user=user)
            except UserAccount.DoesNotExist:
                return Response({
                    "status":"error",
                    "message":"User doesn't have an account yet"
                }, status=status.HTTP_404_NOT_FOUND)  

            if user_account.is_deleted:
                return Response({
                    "status":"error",
                    "message":"User account has been deleted."
                }, status=status.HTTP_400_BAD_REQUEST) 
             


            refresh_token = RefreshToken.for_user(user)
            access_token = str(refresh_token.access_token)
            
            response = Response({
                "status": "success",
                "auth": True,
                "token": access_token,
                "message": "Login successful",
            }, status=status.HTTP_201_CREATED)

            set_jwt_cookies(response, refresh_token, access_token)

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
        auth.logout(request)

        res = Response({
            "status":"success",
            "authenticated": False,
            "message":"You logged out sucessfull"
        }, status=status.HTTP_200_OK)

        remove_jwt_cookies(res)

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


from django.core.validators import validate_email
from django.core.exceptions import ValidationError


@api_view(["POST"])
@permission_classes([AllowAny])
# @authentication_classes([])
def user_feedback(request):
    data = request.data
    full_name = data.get("full_name")
    email = data.get("email")
    message = data.get("message")
    subject = data.get("subject", "General Feedback")

    if not all([full_name, email, message]):
        return Response({
            "status":"error",
            "message":"All fields are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_email(email)
    except ValidationError:
        return Response({
            "status":"error",
            "message":"Invalid email address"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        UserFeedback.objects.create(
            user=None,
            full_name=full_name,
            message=message,
            email=email,
            subject=subject
        )

        return Response({
            "status":"success",
            "message":"Your feedback has been received. Thank you!"
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"An unexpected error occurred. Please try again later. {e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
@permission_classes([IsStaffUser])
def get_feedback(request):

    try:

        feedback = UserFeedback.objects.all().order_by('-sent_at')

        feedback_serializer = UserFeedbackSerializer(feedback, many=True)

        return Response({
            "status":"success",
            "message":"ok",
            "feedback": feedback_serializer.data
        }, status=status.HTTP_200_OK)


    except Exception as e:
        return Response({
            "status":"error",
            "message":f"An unexpected error occured"            
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
@permission_classes([IsStaffUser])
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
@permission_classes([IsStaffUser])
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
                "message": f"{email} is already an admin"
            },status=status.HTTP_404_NOT_FOUND)
            
        except User.DoesNotExist:
            return Response({
                "status":"error",
                "message": f"User with {email} not found"
            },status=status.HTTP_404_NOT_FOUND)
                
        user.is_staff = True
        user.save()

        return Response({
            "status":"error",
            "message": f"{email} has been granted admin status"
        },status=status.HTTP_200_OK)
    

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_user_account(request):
    try:
        try:
            user = UserAccount.objects.get(user=request.user)
        except UserAccount.DoesNotExist:   
            return Response({
                "status":"error",
                "message":"User doesn't have an account yet"
            }, status=status.HTTP_404_NOT_FOUND)  
        
        user.is_deleted = True
        user.save()

        return Response({
            "status":"success",
            "message":"Your account has been deleted."
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        