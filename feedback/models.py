from django.db import models
from django.conf import settings
from cars.models import Car
from rentals.models import Rental  # if Rental is in a different app named `rentals`

class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, null=True, blank=True)
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE ,null=True, blank=True)
    comment = models.TextField()
    feedback_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback #{self.feedback_id} by {self.user}"
