

from django.utils import timezone
from .models import MaintenanceRecord

def calculate_breakdown_risk(car):
    risk_score = 0

    # --- Mileage Risk ---
    if car.mileage > 400000:
        risk_score += 40
    elif car.mileage > 300000:
        risk_score += 30
    elif car.mileage > 100000:
        risk_score += 15

    # --- Maintenance Delay Risk ---
    if car.last_maintenance_date:
        duration = (timezone.now().date() - car.last_maintenance_date).days
    else:
        duration = 999  # Assume very high if never maintained

    if duration > 5:
        risk_score += 50
    elif duration > 3:
        risk_score += 25
    elif duration > 1:
        risk_score += 15

    # --- Rental Duration Risk ---
    if car.total_rental_duration > 5:
        risk_score += 30
    elif car.total_rental_duration > 3:
        risk_score += 10

    # --- Age Risk ---
    age = timezone.now().year - car.year
    if age > 9:
        risk_score += 30
    elif age > 4:
        risk_score += 15

    # --- German Car Risk ---
    if car.is_german:
        risk_score += 30

    # --- Final Risk Assignment ---
    if risk_score >= 70:
        car.breakdown_risk = "High"
        # MaintenanceRecord.objects.get_or_create(car=car, issue_detected="Predicted failure")
    elif risk_score >= 40:
        car.breakdown_risk ="Moderate"
    else:
        car.breakdown_risk ="Low"

    car.save()



def calculate_dynamic_rent(car):
    base_price = car.daily_rate
   # min_base_price = 30  # Minimum rent allowed

    # --- German Car Premium ---
    if car.is_german:
        base_price += 500

    # --- Mileage Deduction ---
    if car.mileage >= 500000:
        base_price -= 200
    elif car.mileage >= 300000:
        base_price -= 100
    elif car.mileage > 200000:
        base_price -= 50

    # --- Age Deduction ---
    age = timezone.now().year - car.year
    if age > 9:
        base_price -= 200
    elif age > 4:
        base_price -= 100

    # --- Maintenance Bonus ---
    if car.last_maintenance_date:
        duration = (timezone.now().date() - car.last_maintenance_date).days
        if duration < 2:
            base_price += 300
        elif duration < 5:
            base_price += 200

    # --- Risk Penalty ---
    if car.breakdown_risk == "High":
        base_price -= 200
    elif car.breakdown_risk == "Moderate":
        base_price -= 100

    # --- Enforce Minimum Price ---
    #car.dynamic_daily_rate = max(base_price, min_base_price)
    car.dynamic_daily_rate = base_price
    car.save()
