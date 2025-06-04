from django.conf import settings
from django.db import models
from cars.models import Car

class Rental(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    rental_start = models.DateTimeField()
    rental_end = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    receipt = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=[
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ])

    def __str__(self):
        return f"{self.receipt} - {self.user.username}"






