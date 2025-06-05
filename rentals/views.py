from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Rental
from django.contrib.auth.models import User
from cars.models import Car
import json
import requests
import base64
import os
from datetime import datetime
from django.utils import timezone
from decimal import Decimal

from django.core.mail import send_mail
from django.conf import settings


from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from cars.models import Car
from .models import Rental
from datetime import datetime


from users.models import CustomUser  


#save amount to admn balance
#save duration to tala milage

@api_view(['POST'])
@permission_classes([AllowAny])
def callback(request):
     return JsonResponse({'success': True, 'message': 'callback endpoint'})


# Check overlap between two date ranges
def is_car_booked(car_id, start, end):
    return Rental.objects.filter(
        car_id=car_id,
        rental_end__gte=start,
        rental_start__lte=end
    ).exists()


# --- M-Pesa Credentials (Hardcoded) ---
MPESA_SHORTCODE = 174379
MPESA_PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
MPESA_CONSUMER_KEY = "YPEGEcAMRuPHQ6AMAZfERSs4uDtGkCi5"
MPESA_CONSUMER_SECRET = "cEqsWn1ejW4fYAYL"
MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"

# --- Get M-Pesa Access Token ---
def get_access_token():
    auth = base64.b64encode(f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}

    response = requests.get(
        f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
        headers=headers
    )
    response.raise_for_status()
    return response.json()["access_token"]

# --- Get Timestamp ---
def get_timestamp():
    return datetime.now().strftime('%Y%m%d%H%M%S')

# --- Generate Password ---
def generate_password(shortcode, passkey, timestamp):
    data = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data.encode()).decode()

# --- Initiate STK Push ---
def initiate_stk_push(phone, amount, service_name):
    try:
        access_token = get_access_token()
    except Exception as e:
        print(f"[ACCESS TOKEN ERROR]: {e}")
        return None

    timestamp = get_timestamp()
    password = generate_password(MPESA_SHORTCODE, MPESA_PASSKEY, timestamp)

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL":'https://astranet.co.ke/stk/callback_url.php', #"https://98f3-197-136-187-86.ngrok-free.app/api/rentals/callback/",
        "AccountReference": f"Car Rental payment - {service_name}",
        "TransactionDesc": f"Car Rental payment - {service_name}"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # Optional: log full response
        #print(f"[STK RESPONSE]: {data}")

        return data.get("CheckoutRequestID")
    except Exception as e:
        print(f"[STK PUSH ERROR]: {e}")
        return None



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rent_car(request):
    data = json.loads(request.body)
    user = request.user

    try:
        car = Car.objects.get(id=data['car_id'])
    except Car.DoesNotExist:
        return JsonResponse({'error': 'Car not found'}, status=404)

    rental_start = data['rental_start']
    rental_end = data['rental_end']
    total_cost = int(data['total_cost'])
    phone_number = data.get('phone_number')

    # 1. Check if car is already booked
    if is_car_booked(car.id, rental_start, rental_end):
        return JsonResponse({'success': False, 'message': 'Car is already booked during that period'}, status=409)

    # 2. Initiate STK Push
    phone = getattr(user, 'contact', None) or phone_number
    service_name = f"{car.year} {car.model}"

    checkout_id = initiate_stk_push(phone, total_cost, service_name)
    if not checkout_id:
        return JsonResponse({'success': False, 'message': 'STK Push failed'}, status=500)

    # 3. Proceed to save rental
    rental = Rental.objects.create(
        user=user,
        car=car,
        rental_start=rental_start,
        rental_end=rental_end,
        total_cost=total_cost,
        status='active',
        receipt=checkout_id
    )


    


    admin_users = CustomUser.objects.filter(role='admin')

    for admin in admin_users:
    # Convert total_cost to Decimal
      total_cost_decimal = Decimal(str(total_cost))
    
    # Ensure admin.balance is not None
      if admin.balance is None:
         admin.balance = Decimal('0.00')
    
    # Safely update the balance
    admin.balance += total_cost_decimal
    admin.save()



    # Parse if input is a string with only the date
    start_dt = datetime.strptime(rental_start, '%Y-%m-%d').date()
    end_dt = datetime.strptime(rental_end, '%Y-%m-%d').date()

    rental_days = (end_dt - start_dt).days
    car.total_rental_duration += rental_days
    car.save()



    # 6. Send confirmation email
    subject = "Rental Confirmation"
    html_message = render_to_string("emails/rental_confirmation.html", {
        'user': user,
        'car': car,
        'rental': rental,
        'theme': {
            'primary': '#1a3a5f',
            'primary_light': '#2c5282',
            'secondary': '#ff6b35',
            'light_gray': '#f8f9fa',
            'dark_gray': '#343a40',
            'white': '#ffffff',
        }
    })
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, 'no-reply@yourapp.com', [user.email], html_message=html_message)

    return JsonResponse({'success': True, 'message': 'Rental created', 'receipt': checkout_id})



@api_view(['GET'])
@permission_classes([AllowAny])
def stats(request):
    try:
        # Get the current logged-in user
        user = request.user

        # Get all active rentals for the user
        active_rentals = Rental.objects.filter(user=user, status__in=['ongoing','active'])

        # Count total bookings and total amount spent where status is not canceled
        total_bookings = active_rentals.exclude(status='cancelled').count()
        total_amount_spent = active_rentals.exclude(status='cancelled').aggregate(Sum('total_cost'))['total_cost__sum'] or 0

        # Determine the membership status based on total bookings
        if total_bookings == 0:
           membership_status = 'Starter'
        elif 1 <= total_bookings <= 2:
              membership_status = 'Bronze'
        elif 3 <= total_bookings <= 4:
                 membership_status = 'Silver'
        else:
            membership_status = 'Gold'


        # Return the statistics in the response
        return Response({
            "success": True,
            "message": "User statistics retrieved successfully",
            "data": {
                "active_rentals": total_bookings,
                "total_amount_spent": total_amount_spent,
                "membership_status": membership_status,
                'total_bookings':total_bookings,
            }
        }, status=200)

    except Exception as e:
        return Response({"success": False, "message": f"Error retrieving stats: {str(e)}"}, status=500)



"""
@api_view(['GET'])
@permission_classes([AllowAny])
def active_rentals(request):
    try:
        user = request.user
        base_url = "https://drivemate-1.onrender.com"  # Explicit base URL

        active_rentals = Rental.objects.filter(
            user=user,
            status='active',
            rental_end__gte=timezone.now()
        ).select_related('car').order_by('rental_start')

        rentals_data = []
        for rental in active_rentals:
            # Process car image URL
            if rental.car.image_url:
                image_url = f"{base_url.rstrip('/')}/{rental.car.image_url.lstrip('/').replace('\\', '/')}"
            else:
                image_url = None

            rentals_data.append({
                "receipt": rental.receipt,
                "car": {
                    "car_id": rental.car.id,
                    "plate_number": rental.car.plate_number,
                    "model": rental.car.model,
                    "category": rental.car.category,
                    "year": rental.car.year,
                    "transmission": rental.car.transmission,
                    "fuel_type": rental.car.fuel_type,
                    "image_url": image_url,  # Properly formatted URL
                },
                "rental_start": rental.rental_start,
                "rental_end": rental.rental_end,
                "total_cost": rental.total_cost,
                "rental_id": rental.id
            })

        return Response({
            "success": True,
            "message": "Active rentals retrieved successfully",
            "rentals": rentals_data
        }, status=200)

    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving active rentals: {str(e)}"
        }, status=500)
"""
@api_view(['GET'])
@permission_classes([AllowAny])
def active_rentals(request):
    try:
        user = request.user
        base_url = "https://drivemate-1.onrender.com"  # Explicit base URL

        active_rentals = Rental.objects.filter(
            user=user,
            status='active',
            rental_end__gte=timezone.now()
        ).select_related('car').order_by('rental_start')

        rentals_data = []
        for rental in active_rentals:
            # Process car image URL
            if rental.car.image_url:
                # First replace backslashes, then handle slashes
                normalized_path = rental.car.image_url.replace('\\', '/')
                image_url = f"{base_url.rstrip('/')}/{normalized_path.lstrip('/')}"
            else:
                image_url = None

            rentals_data.append({
                "receipt": rental.receipt,
                "car": {
                    "car_id": rental.car.id,
                    "plate_number": rental.car.plate_number,
                    "model": rental.car.model,
                    "category": rental.car.category,
                    "year": rental.car.year,
                    "transmission": rental.car.transmission,
                    "fuel_type": rental.car.fuel_type,
                    "image_url": image_url,
                },
                "rental_start": rental.rental_start,
                "rental_end": rental.rental_end,
                "total_cost": rental.total_cost,
                "rental_id": rental.id
            })

        return Response({
            "success": True,
            "message": "Active rentals retrieved successfully",
            "rentals": rentals_data
        }, status=200)

    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving active rentals: {str(e)}"
        }, status=500)





@api_view(['GET'])
@permission_classes([AllowAny])
def past_rentals(request):
    try:
        user = request.user

        if not user or user.is_anonymous:
            return Response({
                "success": False,
                "message": "Authentication required to view past rentals."
            }, status=401)

        # Fetch past rentals excluding cancelled ones, and limit fields for optimization
        past_rentals = (
           Rental.objects
           .filter(user=user, rental_end__lt=timezone.now())
           .exclude(status='cancelled')
           .select_related('car')
           .only('receipt', 'rental_start', 'rental_end', 'total_cost',
          'car__plate_number', 'car__model', 'car__category', 'car__daily_rate')
           .order_by('-rental_end')  # Most recent first
           )
        """
        past_rentals = (
            Rental.objects
            .filter(user=user, rental_end__lt=timezone.now())
            .exclude(status='cancelled')
            .select_related('car')
            .only('receipt', 'rental_start', 'rental_end', 'total_cost',
                  'car__plate_number', 'car__model', 'car__category', 'car__daily_rate')
        )
        """
        
        rentals_data = [
            {
                "receipt": rental.receipt,
                "car": {
                    "plate_number": rental.car.plate_number,
                    "model": rental.car.model,
                    "category": rental.car.category,
                    "daily_rate": rental.car.daily_rate,
                },
                "rental_start": rental.rental_start,
                "rental_end": rental.rental_end,
                "total_cost": rental.total_cost
            }
            for rental in past_rentals
        ]

        return Response({
            "success": True,
            "message": "Past rentals retrieved successfully",
            "data": rentals_data
        }, status=200)

    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving past rentals: {str(e)}"
        }, status=500)






@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_rental(request):
    try:
        rental_id = request.data.get('rental_id')

        if not rental_id:
            return Response({"success": False, "message": "Rental ID is required"}, status=400)

        #rental = Rental.objects.filter(id=rental_id, status='ongoing').first()
        rental = Rental.objects.filter(receipt=rental_id).exclude(status='cancelled').first()


        if not rental:
            return Response({"success": False, "message": "Rental not found or already cancelled"}, status=404)

        # Update rental status to cancelled
        rental.status = 'cancelled'
        rental.save()

        # Send email notification to the user
        subject = f"Rental Cancellation - Ticket "#{rental.receipt}"
        message = f"Dear {rental.user.first_name},\n\nWe regret to inform you that your rental of ticket number {rental.receipt} has been cancelled.\n\nTotal amount: KES {rental.total_cost} will be refunded within 24HRS.\nIf you have any questions, please contact us.\n\nBest regards,\nDriveMate"
        from_email = settings.EMAIL_HOST_USER
        to_email = rental.user.email  # Get the email of the associated user

        send_mail(subject, message, from_email, [to_email])

        return Response({"success": True, "message": f"Rental of ticket {rental.receipt} has been cancelled and email sent."}, status=200)

    except Exception as e:
        return Response({"success": False, "message": f"Error cancelling rental: {str(e)}"}, status=500)

from datetime import timedelta
from django.utils.timezone import now




from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
@permission_classes([AllowAny])
def admin_stats(request):
    total_clients = CustomUser.objects.filter(role='client').count()
    #admin_balance = CustomUser.objects.get(role='admin').balance#aggregate(balance=Sum('balance'))['balance'] or 0
    admin_balance = CustomUser.objects.get(role='admin').balance 
    total_vehicles = Car.objects.count()
    total_bookings = Rental.objects.exclude(status='cancelled').count()


    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_of_day = timezone.make_aware(datetime.combine(today, datetime.max.time()))

   # Count rentals that are active at any point today
    rented_today = Rental.objects.filter(
    rental_start__lte=end_of_day,  # Rental starts today or earlier
    rental_end__gte=start_of_day   # Rental ends today or later
   ).count()


    # Count available cars (cars not rented today)
    available_cars = total_vehicles - rented_today

    # Count cars that need repair (based on last maintenance date or risk status)
    cars_in_repair = Car.objects.filter(status='maintenance').count()
    high_risk_cars = Car.objects.filter(breakdown_risk='High').count()

    return JsonResponse({
        'success': True,
        'data': {
            'total_clients': total_clients,
            'admin_balance': admin_balance,
            'total_vehicles': total_vehicles,
            'total_bookings': total_bookings,
            'rented_today': rented_today,
            'available_cars': available_cars,
            'cars_in_repair': cars_in_repair,
            'high_risk_cars': high_risk_cars,
        }
    })









@api_view(['GET'])
@permission_classes([AllowAny])
def rentals(request):
    
    rentals = Rental.objects.select_related('user', 'car').order_by('-rental_start')
    data = [{
        'receipt': r.receipt,
        'status': r.status,
        'rental_start': r.rental_start,
        'rental_end': r.rental_end,
        'total_cost': float(r.total_cost),
        'user': {
           'name': f"{r.user.first_name} {r.user.last_name or ''}".strip(),
           'email': r.user.email,
           'dp': r.user.profile_picture
           },

        'car': {
            'plate': r.car.plate_number,
            'model': r.car.model,
            'category': r.car.category,
             'year': r.car.year
        }
    } for r in rentals]

    #return Response({'success': True, 'data': data})
    return Response(data)
    #return JsonResponse(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def report_generation_data(request):
    revenue = Rental.objects.exclude(status='cancelled').aggregate(rev=Sum('total_cost'))['rev'] or 0
   # admin_balance = CustomUser.objects.filter(role='admin').aggregate(bal=Sum('balance'))['bal'] or 0
    admin_balance = CustomUser.objects.get(role='admin').balance
    total_cars = Car.objects.count()


    
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_of_day = timezone.make_aware(datetime.combine(today, datetime.max.time()))
   # Count rentals that are active at any point today
    rented = Rental.objects.filter(
    rental_start__lte=end_of_day,  # Rental starts today or earlier
    rental_end__gte=start_of_day   # Rental ends today or later
   ).count()
    """
    # Get today's date
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_of_day = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    rented= Rental.objects.filter(rental_start__gte=start_of_day, rental_end__lte=end_of_day).count()
    """
    
    available = total_cars-rented#Car.objects.filter(status='available').count()
    maintenance = Car.objects.filter(breakdown_risk='High').count()
    #total_users = CustomUser.objects.count()
    total_users=CustomUser.objects.filter(role='client').count()

    last_7_days = now() - timedelta(days=7)
    recent_rentals = Rental.objects.filter(rental_start__gte=last_7_days, status__in=['active', 'ongoing', 'completed'])
    rentals_summary = recent_rentals.values('car__model').annotate(count=Count('id'))

    car_activity = {entry['car__model']: entry['count'] for entry in rentals_summary}

    return Response({
        'success': True,
        'data': {
            'total_revenue': revenue,
            'admin_balance': admin_balance,
            'total_cars': total_cars,
            'rented_cars': rented,
            'available_cars': available,
            'maintenance_cars': maintenance,
            'total_users': total_users,
            'rentals_last_7_days': car_activity
        }#Pass#254//.../kl
    })
