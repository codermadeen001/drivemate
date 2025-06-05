from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Car
import os
import cloudinary.uploader





from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
#from .models import Car, MaintenanceRecord
#from .utils import calculate_dynamic_rent  # if it's in a utils.py file



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
import os

#from .models import Car, Feedback, Rental  # Ensure these are correctly imported
from feedback.models import Feedback
from feedback.models import Rental



from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.utils import timezone
import cloudinary
import cloudinary.uploader





@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_car(request):
    try:
        print("Car creation request received")  # Simple debug print
        
        # Log the incoming data for debugging
        print(f"POST data: {request.POST}")
        print(f"FILES data: {list(request.FILES.keys())}")
        
        # Extract form data
        plate_number = request.POST.get('plate_number')
        model = request.POST.get('model', '').lower().strip()
        transmission = request.POST.get('transmissition')  # Note: keeping the typo from frontend
        year = request.POST.get('year')
        category = request.POST.get('category')
        fuel_type = request.POST.get('fuel_type')
        mileage = request.POST.get('mileage')
        daily_rate = request.POST.get('daily_rate')
        image = request.FILES.get('image')

        # Validate required fields
        required_fields = {
            'plate_number': plate_number,
            'model': model,
            'year': year,
            'category': category,
            'fuel_type': fuel_type,
            'mileage': mileage,
            'daily_rate': daily_rate,
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            print(f"Missing required fields: {missing_fields}")
            return JsonResponse({
                "success": False, 
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }, status=400)

        # Validate image
        if not image:
            print("No image file provided")
            return JsonResponse({
                "success": False, 
                "message": "Image file is required."
            }, status=400)

        # Validate image file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if hasattr(image, 'content_type') and image.content_type not in allowed_types:
            print(f"Invalid image type: {image.content_type}")
            return JsonResponse({
                "success": False, 
                "message": "Invalid image format. Please upload JPG, PNG, GIF, or WebP files only."
            }, status=400)

        # Validate image size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if hasattr(image, 'size') and image.size > max_size:
            print(f"Image too large: {image.size} bytes")
            return JsonResponse({
                "success": False, 
                "message": "Image file is too large. Maximum size is 10MB."
            }, status=400)

        # Check if plate number already exists
        if Car.objects.filter(plate_number=plate_number).exists():
            print(f"Duplicate plate number: {plate_number}")
            return JsonResponse({
                "success": False, 
                "message": "A car with this plate number already exists."
            }, status=400)

        print("Starting Cloudinary upload")
        
        # Upload to Cloudinary with error handling
        try:
            upload_result = cloudinary.uploader.upload(
                image, 
                folder="cars/",
                resource_type="image",
                allowed_formats=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                max_file_size=10000000  # 10MB
            )
            image_url = upload_result.get("secure_url")
            print(f"Cloudinary upload successful: {image_url}")
        except Exception as cloudinary_error:
            print(f"Cloudinary upload failed: {str(cloudinary_error)}")
            return JsonResponse({
                "success": False, 
                "message": f"Image upload failed: {str(cloudinary_error)}"
            }, status=500)

        # German brand check
        german_brands = ['bmw', 'mercedes', 'mercedes benz', 'audi', 'volkswagen', 'porsche', 'opel']
        model_words = model.split()
        brand_candidate = ' '.join(model_words[:2]) if len(model_words) >= 2 else ''
        brand_candidate_single = model_words[0] if model_words else ''
        is_german = brand_candidate in german_brands or brand_candidate_single in german_brands

        print("Creating car record in database")
        
        # Convert and validate numeric fields
        try:
            year = int(year)
            mileage = int(mileage)
            daily_rate = float(daily_rate)
        except ValueError as ve:
            print(f"Invalid numeric data: {str(ve)}")
            return JsonResponse({
                "success": False, 
                "message": "Invalid numeric data provided."
            }, status=400)

        # Save to DB
        try:
            car = Car.objects.create(
                plate_number=plate_number,
                model=model,
                transmission=transmission,
                year=year,
                category=category,
                fuel_type=fuel_type,
                last_maintenance_date=timezone.now().date(),
                is_german=is_german,
                mileage=mileage,
                daily_rate=daily_rate,
                dynamic_daily_rate=daily_rate,
                image_url=image_url
            )
            print(f"Car created successfully with ID: {car.id}")
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            return JsonResponse({
                "success": False, 
                "message": f"Database error: {str(db_error)}"
            }, status=500)

        return JsonResponse({
            "success": True,
            "message": "Car created successfully!",
            "car_id": car.id,
            "image_url": car.image_url,
            "plate_number": car.plate_number,
            "model": car.model
        })

    except Exception as e:
        print(f"Unexpected error in create_car: {str(e)}")
        return JsonResponse({
            "success": False,
            "message": f"An unexpected error occurred: {str(e)}"
        }, status=500)

"""
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_car(request):
    try:
        plate_number = request.POST.get('plate_number')
        model = request.POST.get('model', '').lower().strip()
        transmission = request.POST.get('transmissition')
        year = request.POST.get('year')
        category = request.POST.get('category')
        fuel_type = request.POST.get('fuel_type')
        mileage = request.POST.get('mileage')
        daily_rate = request.POST.get('daily_rate')
        image = request.FILES.get('image')

        if not image:
            return JsonResponse({"success": False, "message": "Image file is required."}, status=400)

        # 🔥 Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(image, folder="cars/")
        image_url = upload_result.get("secure_url")

        # German brand check
        german_brands = ['bmw', 'mercedes', 'mercedes benz', 'audi', 'volkswagen', 'porsche', 'opel']
        model_words = model.split()
        brand_candidate = ' '.join(model_words[:2])
        brand_candidate_single = model_words[0] if model_words else ''
        is_german = brand_candidate in german_brands or brand_candidate_single in german_brands

        # Save to DB
        car = Car.objects.create(
            plate_number=plate_number,
            model=model,
            transmission=transmission,
            year=year,
            category=category,
            fuel_type=fuel_type,
            last_maintenance_date=timezone.now().date(),
            is_german=is_german,
            mileage=mileage,
            daily_rate=daily_rate,
            dynamic_daily_rate=daily_rate,
            image_url=image_url
        )

        return JsonResponse({
            "success": True,
            "message": "Car created successfully.",
            "car_id": car.id,
            "image_url": car.image_url
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }, status=500)



"""


"""
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_car(request):
    try:
        plate_number = request.POST.get('plate_number')
        model = request.POST.get('model', '').lower().strip()
        transmission = request.POST.get('transmissition')
        year = request.POST.get('year')
        category = request.POST.get('category')
        fuel_type = request.POST.get('fuel_type')
        mileage = request.POST.get('mileage')
        daily_rate = request.POST.get('daily_rate')
        #make = request.POST.get('make')

        image = request.FILES.get('image')
        if not image:
            return JsonResponse({"success": False, "message": "Image file is required."}, status=400)

        # Create folder if it doesn't exist
        image_folder = os.path.join(settings.MEDIA_ROOT, 'cars')
        os.makedirs(image_folder, exist_ok=True)

        image_name = image.name
        image_path = os.path.join('cars', image_name)
        full_path = os.path.join(settings.MEDIA_ROOT, image_path)

        with open(full_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)

        model = request.POST.get('model', '').lower().strip()

        # List of known German car brands
        german_brands = ['bmw', 'mercedes', 'mercedes benz', 'audi', 'volkswagen', 'porsche', 'opel']
        # Split the model into words and only check the first one or two as brand indicators
        model_words = model.split()
        # Create a string of the first two words to catch things like "Mercedes Benz"
        brand_candidate = ' '.join(model_words[:2])  # e.g., "mercedes benz"
        brand_candidate_single = model_words[0] if model_words else ''
        # Check if either matches a German brand
        is_german = brand_candidate in german_brands or brand_candidate_single in german_brands


        # Save to DB
        car = Car.objects.create(
            plate_number=plate_number,
            #make=make,
            model=model,
            transmission=transmission,
            year=year,
            category=category,
            fuel_type=fuel_type,
            last_maintenance_date=timezone.now().date(),
            is_german=is_german,
            mileage=mileage,
            daily_rate=daily_rate,
            dynamic_daily_rate=daily_rate,
            image_url=os.path.join(settings.MEDIA_URL, image_path)
        )

        return JsonResponse({
            "success": True,
            "message": "Car created successfully.",
            "car_id": car.id,
            "image_url": car.image_url
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }, status=500)








@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_cars(request):
    try:
        cars = Car.objects.all()
        base_url = "https://drivemate-1.onrender.com"  # Explicit base URL
        
        data = []
        for car in cars:
            # Process image URL
            if car.image_url:
                # Normalize path and join with base URL
                image_url = f"{base_url.rstrip('/')}/{car.image_url.lstrip('/').replace('\\', '/')}"
            else:
                image_url = None

            data.append({
                "id": car.id,
                "plate_number": car.plate_number,
                "model": car.model,
                "transmission": car.transmission,
                "year": car.year,
                "category": car.category,
                "fuelType": car.fuel_type,
                "mileage": car.mileage,
                "daily_rate": str(car.daily_rate),
                "dynamic_daily_rate": str(car.dynamic_daily_rate) if car.dynamic_daily_rate else None,
                "status": car.status,
                "breakdown_risk": car.breakdown_risk,
                "image_url": image_url,
                "created_at": car.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return JsonResponse({"success": True, "data": data})
    
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error fetching cars: {str(e)}"}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def car_data(request):
    try:
        car_id = request.data.get('car_id')
        if not car_id:
            return Response({"success": False, "message": "car_id is required."}, status=400)

        car = get_object_or_404(Car, id=car_id)
        base_url = request.build_absolute_uri('/')[:-1]
        # "image_url": (base_url + car.image_url).replace('\\', '/'),
        car_info = {
            "id": car.id,
            "plate_number": car.plate_number,
            "model": car.model,
            "transmission": car.transmission,
            "year": car.year,
            "category": car.category,
            "fuelType": car.fuel_type,
            "mileage": car.mileage,
            "daily_rate": str(car.daily_rate),
            "dynamic_daily_rate": str(car.dynamic_daily_rate) if car.dynamic_daily_rate else None,
            "status": car.status,
            "image_url": (base_url + car.image_url).replace('\\', '/'),
            "created_at": car.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

        return Response({"success": True, "data": car_info}, status=200)

    except Exception as e:
        return Response({"success": False, "message": f"Error fetching car: {str(e)}"}, status=500)
"""

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_cars(request):
    try:
        cars = Car.objects.all()
        data = []
        for car in cars:
            image_url = car.image_url if car.image_url else None

            data.append({
                "id": car.id,
                "plate_number": car.plate_number,
                "model": car.model,
                "transmission": car.transmission,
                "year": car.year,
                "category": car.category,
                "fuelType": car.fuel_type,
                "mileage": car.mileage,
                "daily_rate": str(car.daily_rate),
                "dynamic_daily_rate": str(car.dynamic_daily_rate) if car.dynamic_daily_rate else None,
                "status": car.status,
                "breakdown_risk": car.breakdown_risk,
                "image_url": image_url,
                "created_at": car.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return JsonResponse({"success": True, "data": data})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error fetching cars: {str(e)}"}, status=500)







@api_view(['POST'])
@permission_classes([AllowAny])
def car_data(request):
    try:
        car_id = request.data.get('car_id')
        if not car_id:
            return Response({"success": False, "message": "car_id is required."}, status=400)

        car = get_object_or_404(Car, id=car_id)

        image_url = car.image_url if car.image_url else None

        car_info = {
            "id": car.id,
            "plate_number": car.plate_number,
            "model": car.model,
            "transmission": car.transmission,
            "year": car.year,
            "category": car.category,
            "fuelType": car.fuel_type,
            "mileage": car.mileage,
            "daily_rate": str(car.daily_rate),
            "dynamic_daily_rate": str(car.dynamic_daily_rate) if car.dynamic_daily_rate else None,
            "status": car.status,
            "image_url": image_url,
            "created_at": car.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

        return Response({"success": True, "data": car_info}, status=200)

    except Exception as e:
        return Response({"success": False, "message": f"Error fetching car: {str(e)}"}, status=500)


"""


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_cars(request):
    try:
        cars = Car.objects.all()
        base_url = "https://drivemate-1.onrender.com"  # Explicit base URL
        
        data = []
        for car in cars:
            if car.image_url:
                # Normalize image URL by replacing backslashes and stripping leading slash
                normalized_image_path = car.image_url.replace('\\', '/').lstrip('/')
                image_url = f"{base_url}/{normalized_image_path}"
            else:
                image_url = None

            data.append({
                "id": car.id,
                "plate_number": car.plate_number,
                "model": car.model,
                "transmission": car.transmission,
                "year": car.year,
                "category": car.category,
                "fuelType": car.fuel_type,
                "mileage": car.mileage,
                "daily_rate": str(car.daily_rate),
                "dynamic_daily_rate": str(car.dynamic_daily_rate) if car.dynamic_daily_rate else None,
                "status": car.status,
                "breakdown_risk": car.breakdown_risk,
                "image_url": image_url,
                "created_at": car.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return JsonResponse({"success": True, "data": data})
    
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error fetching cars: {str(e)}"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def car_data(request):
    try:
        car_id = request.data.get('car_id')
        if not car_id:
            return Response({"success": False, "message": "car_id is required."}, status=400)

        car = get_object_or_404(Car, id=car_id)
        
        base_url = "https://drivemate-1.onrender.com"  # Use same base URL explicitly here too
        if car.image_url:
            normalized_image_path = car.image_url.replace('\\', '/').lstrip('/')
            image_url = f"{base_url}/{normalized_image_path}"
        else:
            image_url = None

        car_info = {
            "id": car.id,
            "plate_number": car.plate_number,
            "model": car.model,
            "transmission": car.transmission,
            "year": car.year,
            "category": car.category,
            "fuelType": car.fuel_type,
            "mileage": car.mileage,
            "daily_rate": str(car.daily_rate),
            "dynamic_daily_rate": str(car.dynamic_daily_rate) if car.dynamic_daily_rate else None,
            "status": car.status,
            "image_url": image_url,
            "created_at": car.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

        return Response({"success": True, "data": car_info}, status=200)

    except Exception as e:
        return Response({"success": False, "message": f"Error fetching car: {str(e)}"}, status=500)


"""











@api_view(['POST'])
@permission_classes([AllowAny])
def maintance(request):
    car_id = request.data.get('car_id')
   
    try:
        car = Car.objects.get(id=car_id)
        car.last_maintenance_date = timezone.now().date()
        car.total_rental_duration = 0
        car.breakdown_risk = "Low"
        car.dynamic_daily_rate= car.daily_rate
        car.save()

        return JsonResponse({'success': True, 'message': "Maintanace Checked"})

    except Car.DoesNotExist:
       return JsonResponse({'success': False, 'error': 'Car not found'}, status=404)
    
    






@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def delete(request):
    try:
        car_id = request.data.get('car_id')
        if not car_id:
            return Response({'success': False, 'message': 'car_id is required'}, status=400)

        car = get_object_or_404(Car, id=car_id)

        # Delete related feedbacks
        Feedback.objects.filter(car=car).delete()

        # Delete related rentals
        Rental.objects.filter(car=car).delete()

        # Delete image file from storage if exists
        """
        if car.image_url:
            image_path = os.path.join(settings.MEDIA_ROOT, car.image_url.replace(settings.MEDIA_URL, '').replace('/', os.sep))
            if os.path.exists(image_path):
                os.remove(image_path)
        """""
        # Delete the car itself
        car.delete()

        return Response({'success': True, 'message': 'Car and related data deleted successfully.'}, status=200)

    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)









@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def high_risk_cars(request):
    high_risk_cars = Car.objects.filter(breakdown_risk='High')
    car_details = high_risk_cars.values('plate_number', 'year', 'model','breakdown_risk')

    if car_details:
        return JsonResponse({
            'success': True,
            'message': 'High-risk cars retrieved successfully.',
            'data': list(car_details)
        }, status=200)
    else:
        return JsonResponse({
            'success': False,
            'message': 'No high-risk cars found.',
            'data': []
        }, status=200)
