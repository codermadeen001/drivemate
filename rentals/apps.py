from django.apps import AppConfig


class RentalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rentals'


    def ready(self):
        from . import scheduler
        scheduler.start()
