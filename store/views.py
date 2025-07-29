from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from .models import Product, Category
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductSerializer, CategorySerializer, ProductImages
from uuid import UUID
from users.permissions import IsFromAllowedOrigin
from admin_panel.permissions import IsStaffUser
from rest_framework.parsers import MultiPartParser, FormParser

# Create your views here.

@api_view(["GET"])
@permission_classes([IsFromAllowedOrigin])
@authentication_classes([])
def get_products(request):
    try:
        product = Product.objects.filter(not_available=False).select_related("category").prefetch_related("images").order_by('-created_at')

        product_serializer = ProductSerializer(product, many=True)

        return Response({
            "status":"success",
            "message":"ok",
            "product": product_serializer.data
        }, status=status.HTTP_200_OK)


    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(["GET"])
@permission_classes([IsFromAllowedOrigin, IsStaffUser])
def get_all_products(request):
    try:
        product = Product.objects.select_related('category').prefetch_related('images').all().order_by('-created_at')

        product_serializer = ProductSerializer(product, many=True)

        return Response({
            "status":"success",
            "message":"ok",
            "product": product_serializer.data
        }, status=status.HTTP_200_OK)


    except Exception as e:
        return Response({
            "status":"error",
            "message":f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


def get_fallback_products(category_name=None):
    if category_name:
        products = Product.objects.filter(category__name__iexact=category_name)[:3]
    else:
        products = Product.objects.filter(is_new=True)[:3]
    return ProductSerializer(products, many=True).data



@api_view(["GET"])
@authentication_classes([])
def get_product_via_id(request, uuid):
    try:

        try:
            uuid_obj = UUID(uuid)
        except ValueError:

            fallback_data = get_fallback_products(request.query_params.get("category"))

            return Response({
                "status": "error",
                "message": "Product not found",
                "fallback": fallback_data
            }, status=404)


        try:
            product = Product.objects.get(id=uuid)
        except Product.DoesNotExist:
            fallback_data = get_fallback_products(request.query_params.get("category"))

            return Response({
                "status": "error",
                "message": "Product with this ID does not exist",
                "fallback": fallback_data
            }, status=status.HTTP_404_NOT_FOUND)

        product_serializer = ProductSerializer(product)

        related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:6]
        related_serializer = ProductSerializer(related_products, many=True)

        return Response({
            "status": "success",
            "message": "ok",
            "product": product_serializer.data,
            "related": related_serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(["POST"])
@permission_classes([IsFromAllowedOrigin, IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def create_category(request):

    try:
        name = request.data.get('name')
        description = request.data.get('description')
        image_file = request.FILES.get('image')

        if not name or not description or not image_file:
            return Response({
                "status":"error",
                "message": "All fields are required" 
            }, status=status.HTTP_400_BAD_REQUEST)
            

        if Category.objects.filter(name=name).exists():
            return Response({
                "status":"error",
                "message": "Category with this name already exists"
                },status=status.HTTP_409_CONFLICT
            )


        if image_file:
            if not image_file.content_type.startswith('image/'):
                return Response({
                    "status" : "error",
                    "message": "Invalid file type. Only images are allowed"
                    },status=status.HTTP_400_BAD_REQUEST
                )
            

        category = Category.objects.create(name=name, description=description, image=image_file)
        
        return Response({
            "status":"success",
            "message":"Category created successful"
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status": "error",
            "message": f"{str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsFromAllowedOrigin])
@authentication_classes([])
def get_categories(request):

    try:
        category = Category.objects.all()

        category_serializer = CategorySerializer(category, many=True)

        return Response({
            "status": "success",
            "message": "ok",
            "category": category_serializer.data,
        }, status=status.HTTP_200_OK)        

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    




@api_view(["GET"])
@permission_classes([IsFromAllowedOrigin])
@authentication_classes([])
def get_product_via_category(request):

    try:

        category = Category.objects.filter(name=request.query_params.get("category_name"))

        product = Product.objects.filter(category=category)


        product_serializer = ProductSerializer(product, many=True)

        return Response({
            "status": "success",
            "message": "ok",
            "product": product_serializer.data,
        }, status=status.HTTP_200_OK)        

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    



@api_view(['POST'])
@permission_classes([IsStaffUser, IsFromAllowedOrigin])
@parser_classes([MultiPartParser, FormParser])
def create_product(request):
    try:
        category_name = request.data.get('category')

        try:
            category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            return Response({
                "status":"error",
                "message":"category does not exist"
            },status=status.HTTP_404_NOT_FOUND)    


        product = Product.objects.create(
            title=request.data.get('title'),
            description=request.data.get('description'),
            product_image=request.FILES.get('product_image'),
            alt_text=request.data.get('alt_text', ''),
            category=category,
            price=request.data.get('price'),
            discount_price=request.data.get('discount_price'),
            size=request.data.get('size'),
            color=request.data.get('color'),
            stock=request.data.get('stock', 0),
            is_hot=request.data.get('is_hot', False),
            is_new=request.data.get('is_new', False),
            is_best=request.data.get('is_best', False),
            is_trending=request.data.get('is_trending', False),
            is_featured=request.data.get('is_featured', False),
        )

        images = request.FILES.getlist('images')
        for img in images:
            ProductImages.objects.create(product=product, image=img)

        return Response({
            "status":"success",
            "message": "Product created successfully."
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            "status":"error",
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
@permission_classes([IsStaffUser, IsFromAllowedOrigin])
@parser_classes([MultiPartParser, FormParser])
def edit_product(request, product_id):
    try:
        
        try:
            product = Product.objects.get(id=product_id)

        except Product.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Product id does not exists"
        }, status=status.HTTP_404_NOT_FOUND)

        try:
            category = Category.objects.get(name=request.data.get('category'))
        except Category.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Category does not exists"
        }, status=status.HTTP_404_NOT_FOUND)

        product.title = request.data.get('title', product.title)
        product.description = request.data.get('description', product.description)
        product.alt_text = request.data.get('alt_text', product.alt_text)
        product.category = category
        product.price = request.data.get('price', product.price)
        product.discount_price = request.data.get('discount_price', product.discount_price)
        product.size = request.data.get('size', product.size)
        product.color = request.data.get('color', product.color)
        product.stock = request.data.get('stock', product.stock)
        product.is_hot = request.data.get('is_hot', product.is_hot)
        product.is_new = request.data.get('is_new', product.is_new)
        product.is_best = request.data.get('is_best', product.is_best)
        product.is_trending = request.data.get('is_trending', product.is_trending)
        product.is_featured = request.data.get('is_featured', product.is_featured)

        if request.FILES.get('product_image'):
            if product.product_image:
                product.product_image.delete()
                
            product.product_image = request.FILES.get('product_image')

        product.save()

        if 'images' in request.FILES:
            ProductImages.objects.filter(product=product).delete()
            for img in request.FILES.getlist('images'):
                ProductImages.objects.create(product=product, image=img)

        return Response({
            "status":"success",
            "message": "Product updated successfully."
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status":"error",
            "message": f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



@api_view(['POST'])
@permission_classes([IsStaffUser])
def delete_product(request):
    
    product_id = request.data.get("product_id")
    product_action = request.data.get("product_action", False)

    try:
        if not product_id:
            return Response({
                "status":"error",
                "message":"Product Id is required"
            }, status=status.HTTP_400_BAD_REQUEST)


        try:

            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Product ID does not exist"
            }, status=status.HTTP_404_NOT_FOUND)    
        
        product.not_available = product_action
        product.save()

        return Response({
            "status":"success",
            "message": "Product was removed" if product_action  else "Product has been Undeleted"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status":"error",
            "message": f"{e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    