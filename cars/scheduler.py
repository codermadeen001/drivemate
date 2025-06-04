"""from apscheduler.schedulers.background import BackgroundScheduler
from .models import Car
from .utils import calculate_breakdown_risk, calculate_dynamic_rent

def update_car_metrics():
    for car in Car.objects.all():
        calculate_breakdown_risk(car)
        calculate_dynamic_rent(car)

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_car_metrics, 'interval', minutes=15)
    scheduler.start()
"""










from apscheduler.schedulers.background import BackgroundScheduler
from .models import Car
from .utils import calculate_breakdown_risk, calculate_dynamic_rent

def update_car_metrics():
    print("Automatic risk and price calculation is running...")
    for car in Car.objects.all():
        calculate_breakdown_risk(car)
        calculate_dynamic_rent(car)

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_car_metrics, 'interval', minutes=1)
    scheduler.start()
