from django.db import models

class Car(models.Model):
    CATEGORY_CHOICES = [
        ('sedan', 'Sedan'),
        ('SUV', 'SUV'),
        ('Station Wagon', 'Station Wagon'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'Maintenance'),
    ]

    TRANSMISSION_CHOICES = [
        ('automatic', 'automatic'),
        ('manual', 'manual'),
    ]

    FUEL_CHOICES = [
        ('Petrol', 'Petrol'),
        ('Diesel', 'Diesel'),
    ]

    RISKS_CHOICES = [
        ('Low', 'Low'),
        ('High', 'High'),
        ('Moderate', 'Moderate'),
    ]
    
   

    plate_number = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICES)
    fuel_type = models.CharField(max_length=10, choices=FUEL_CHOICES, default='Petrol')
    mileage = models.IntegerField()
    transmission = models.CharField(max_length=15, choices=TRANSMISSION_CHOICES, default='automatic')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)

    dynamic_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    breakdown_risk = models.CharField(choices=RISKS_CHOICES, max_length=15, default="Low")
    total_rental_duration = models.IntegerField(default=0)  # days since last repair
    last_maintenance_date = models.DateField(null=True, blank=True)
    #last_service_date = models.DateTimeField(null=True, blank=True)

    image_url = models.TextField()
    is_german = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.plate_number



    #def is_german(self):
       # return self.model in GERMAN_CARS



class MaintenanceRecord(models.Model):
   car = models.ForeignKey(Car, on_delete=models.CASCADE)
   issue_detected = models.CharField(max_length=100)
   detected_on = models.DateField(auto_now_add=True)
   resolved = models.BooleanField(default=False)