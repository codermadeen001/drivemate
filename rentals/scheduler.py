# scheduler.py
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import now

def check_and_complete_rentals():
    from .models import Rental  

    current_time = now()
    print(f"[{current_time}] Checking rentals...")

    rentals_to_complete = Rental.objects.filter(
        rental_end__lt=current_time
    ).exclude(status__in=['completed', 'cancelled'])

    if rentals_to_complete.exists():
        for rental in rentals_to_complete:
            rental.status = 'completed'
            rental.save()
            print(f"✔ Rental {rental.receipt} marked as completed.")
    else:
        print("No rentals to complete at this time.")

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_complete_rentals, 'interval', minutes=1)
    scheduler.start()
