#python manage.py update_car_metrics
# ncron add '*/30 * * * *' python manage.py update_car_metrics


from django.core.management.base import BaseCommand
from cars.models import Car
from cars.utils import calculate_breakdown_risk, calculate_dynamic_rent


class Command(BaseCommand):
    help = 'Recalculate breakdown risk and rent for all cars'

    def handle(self, *args, **kwargs):
        for car in Car.objects.all():
            calculate_breakdown_risk(car)
            calculate_dynamic_rent(car)
        self.stdout.write(self.style.SUCCESS('Updated breakdown risk and rent for all cars'))




"""

On car changes, cron recalculates rent and risk.

If serviced, it resets total_rental_duration, sets risk to Low, and updates dynamic_rent_fee.

Mileage, age, German brand, and last maintenance time impact risk and rent.

Breakdown predictions automatically create a MaintenanceRecord.
"""