from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from .models import Product, Category
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductSerializer, CategorySerializer, ProductImages
from uuid import UUID
from admin_panel.permissions import IsStaffUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import throttle_classes
from django.views.decorators.cache import cache_page
from utils.cache.cache import set_cached_data, get_cached_data
from utils.cache.category_cache_key import category_cache_key

# Create your views here.

@api_view(["GET"])
@permission_classes([])
@authentication_classes([])
@throttle_classes([])
def get_products(request):
    try:
        cache_key = "all_public_products"
        cached_data = get_cached_data(cache_key)

        if cached_data:
            print("✅ Cache hit: public products")
            return Response({
                "status": "success",
                "message": "ok (from cache)",
                "product": cached_data
            }, status=status.HTTP_200_OK)

        # Fetch from DB if not cached
        products = (
            Product.objects.filter(not_available=False)
            .select_related("category")
            .prefetch_related("images")
            .order_by("-created_at")
        )
        serializer = ProductSerializer(products, many=True)

        # Cache result for a month
        set_cached_data(cache_key, serializer.data)
        print(" Cached public products for 30 days")

        return Response({
            "status": "success",
            "message": "ok",
            "product": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Admin/staff-only products
@api_view(["GET"])
@permission_classes([IsStaffUser])
@throttle_classes([])
def get_all_products(request):
    try:
        cache_key = "all_admin_products"
        cached_data = get_cached_data(cache_key)

        if cached_data:
            return Response({
                "status": "success",
                "message": "ok (from cache)",
                "product": cached_data
            }, status=status.HTTP_200_OK)

        products = (
            Product.objects.select_related("category")
            .prefetch_related("images")
            .order_by("-created_at")
        )
        serializer = ProductSerializer(products, many=True)

        set_cached_data(cache_key, serializer.data)

        return Response({
            "status": "success",
            "message": "ok",
            "product": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_fallback_products(category_name=None):
    if category_name:
        products = Product.objects.filter(category__name__iexact=category_name)[:3]
    else:
        products = Product.objects.filter(is_new=True)[:3]
    return ProductSerializer(products, many=True).data



@api_view(["GET"])
@authentication_classes([])
@throttle_classes([])
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
@permission_classes([IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def create_category(request):
    try:
        name = request.data.get('name')
        description = request.data.get('description')
        image_file = request.FILES.get('image')

        if not all([name, description, image_file]):
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
                    },status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                )
            

        Category.objects.create(name=name, description=description, image=image_file)
        
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
@permission_classes([])
@authentication_classes([])
@throttle_classes([])
def get_categories(request):
    try:
        cache_key = "all_categories"
        cached_data = get_cached_data(cache_key)

        if cached_data:
            return Response({
                "status": "success",
                "message": "ok (from cache)",
                "category": cached_data,
            }, status=status.HTTP_200_OK)

        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)

        set_cached_data(cache_key, serializer.data)
        print(" Cached categories for 30 days")

        return Response({
            "status": "success",
            "message": "ok",
            "category": serializer.data,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([])
@authentication_classes([])
@throttle_classes([])
def get_product_via_category(request):
    query = request.query_params.get("category_name")
    if not query:
        return Response({
            "status": "error",
            "message": "Category name wasn't passed. Please check and try again."
        }, status=status.HTTP_400_BAD_REQUEST)

    cache_key = category_cache_key(query)
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return Response({
            "status": "success",
            "message": "ok (from cache)",
            "product": cached_data,
        }, status=status.HTTP_200_OK)

    try:
        category = Category.objects.filter(name__iexact=query).first()  # case-insensitive match
        if not category:
            return Response({
                "status": "error",
                "message": f"Category '{query}' not found."
            }, status=status.HTTP_404_NOT_FOUND)

        products = Product.objects.filter(category=category).select_related("category").prefetch_related("images").order_by("-created_at")
        serializer = ProductSerializer(products, many=True)

        # Cache for 30 days
        set_cached_data(cache_key, serializer.data, timeout=60 * 60 * 24 * 30)

        return Response({
            "status": "success",
            "message": "ok",
            "product": serializer.data,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsStaffUser, ])
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
@permission_classes([IsStaffUser])
@parser_classes([MultiPartParser, FormParser])
def edit_product(request, product_id):
    category = request.data.get('category')
    try:
        
        try:
            product = Product.objects.get(id=product_id)

        except Product.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Product id does not exists"
        }, status=status.HTTP_404_NOT_FOUND)

        try:
            category = Category.objects.get(name=category)
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