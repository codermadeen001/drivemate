from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password
import random
import string
from  django.shortcuts import render

User = get_user_model()

def generate_token(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


@api_view(['POST'])
@permission_classes([AllowAny])


def index(request):
    return render(request, 'car.html')

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    first_name = request.data.get('firstName')
    last_name = request.data.get('lastName')
    contact = request.data.get('contact')
    email = request.data.get('email')
    password = request.data.get('password')

    if not all([first_name, last_name, email, password]):
        return Response({"success": False, "message": "All required fields must be provided"}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({"success": False, "message": "Account exists!"}, status=409)

    role = 'admin' if email.lower() == 'admin@gmail.com' else 'client'

    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            contact=contact
        )

        try:
            send_mail(
                'Welcome to DriveMate',
                'Your account has been successfully created.',
                'no-reply@groomstyle.com',
                [email],
                fail_silently=True
            )
        except Exception as e:
            print(f"Email error: {e}")

        token = generate_token(user)
        return Response({
            "success": True,
            "message": "Account created successfully",
            "token": token,
            "isAdmin": role == 'admin'
        }, status=201)

    except IntegrityError:
        return Response({"success": False, "message": "Account already exists!"}, status=409)

    except Exception as e:
        return Response({"success": False, "message": f"Signup failed: {str(e)}"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])

def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"success": False, "message": "Email and password are required"}, status=400)

    user = authenticate(request, email=email, password=password)
    if not user:
        return Response({"success": False, "message": "Invalid credentials!"}, status=401)

    if user.role == 'client' and getattr(user, 'suspended', False):
        return Response({"success": False, "message": "Your account has been suspended. Please contact support."}, status=403)

    token = generate_token(user)
    return Response({"success": True, "token": token, "role": user.role}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    userName = request.data.get('userName')
    userEmail = request.data.get('userEmail')
    userImgUrl = request.data.get('userImgUrl')

    if not userEmail:
        return Response({"success": False, "message": "Email is required!"}, status=400)

    try:
        user = User.objects.filter(email=userEmail).first()

        if user:
            if user.role == 'client' and getattr(user, 'suspended', False):
                return Response({
                    "success": False,
                    "message": "Your account has been suspended. Please contact support."
                }, status=403)

            if userImgUrl:
                user.profile_picture = userImgUrl
                user.save()
        else:
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user = User.objects.create(
                email=userEmail,
                password=make_password(random_password),
                first_name=userName,
                profile_picture=userImgUrl or 'http://localhost:8000/media/dp.jpg',
            )

            send_mail(
                'Welcome to DriveMate',
                'Your Google account has been successfully linked to our system.',
                'no-reply@groomstyle.com',
                [userEmail],
                fail_silently=True
            )

        token = generate_token(user)
        return Response({
            "success": True,
            "message": "Login successful",
            "token": token,
            "role": user.role
        })

    except Exception as e:
        return Response({"success": False, "message": f"Google login failed: {str(e)}"}, status=500)




@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset(request):
    email = request.data.get('email')

    if not email:
        return Response({"success": False, "message": "Email is required"}, status=400)

    try:
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"success": False, "message": "No account found with that email"}, status=404)

        # Generate new random password
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        user.password = make_password(new_password)
        user.save()

        try:
            send_mail(
                'Password Reset - DrivMate',
                f'Your new password is: {new_password}\n\nPlease log in and change it immediately.',
                'no-reply@groomstyle.com',
                [email],
                fail_silently=True
            )
        except Exception as email_error:
            print(f"Email sending failed: {email_error}")

        return Response({"success": True, "message": "A new password has been sent to your email"}, status=200)

    except Exception as e:
        return Response({"success": False, "message": f"Password reset failed: {str(e)}"}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_contact(request):
    user = request.user
    new_contact = request.data.get('contact')

    if not new_contact:
        return Response({"success": False, "message": "Contact is required"}, status=400)

    user.contact = new_contact
    user.save()

    return Response({"success": True, "message": "Contact updated successfully"}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_authenticated_user(request):
    user = request.user
    base_url = "https://drivemate-1.onrender.com"
    
    # Process profile picture URL
    if user.profile_picture:
        # Normalize path (replace backslashes with forward slashes)
        normalized_path = user.profile_picture.replace('\\', '/')
        # Join with base URL (avoiding double slashes)
        profile_picture_url = f"{base_url.rstrip('/')}/{normalized_path.lstrip('/')}"
    else:
        profile_picture_url = None

    return Response({
        "success": True,
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": f"{user.first_name} {user.last_name or ''}",
            "email": user.email,
            "contact": user.contact,
            "profile_picture": profile_picture_url,
            "role": user.role
        }
    }, status=200)

"""


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_authenticated_user(request):
    user = request.user
    return Response({
    "success": True,
    "user": {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "name": f"{user.first_name} {user.last_name or ''}",
        "email": user.email,
        "contact": user.contact,
        "profile_picture": request.build_absolute_uri(user.profile_picture) if user.profile_picture else None,
        "role": user.role
    }
}, status=200)




 return Response({
        "success": True,
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
           "name" = f"{user.first_name} {user.last_name or ''}",
            "email": user.email,
            "contact": user.contact,
            "profile_picture":request.build_absolute_uri(user.profile_picture) if user.profile_picture else None,
            "role": user.role
        }
    }, status=200)
"""