from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault('role', 'client')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    contact = models.CharField(max_length=15, unique=True, null=True, blank=True)
    profile_picture = models.CharField(max_length=255, default='http://127.0.0.1:8000/media/dp.jpg', blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True) 
    suspended = models.BooleanField(default=False)
    
    ROLE_CHOICES = [('client', 'Client'), ('admin', 'Admin')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    created_at = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
  

    class Meta:
        unique_together = ('first_name', 'last_name')
    
   

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"
