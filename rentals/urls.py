from django.urls import path
from .views import rent_car, active_rentals, stats, past_rentals,cancel_rental,admin_stats,callback,report_generation_data,rentals

urlpatterns = [
    path('create/', rent_car, name='rent_car'),
    path('callback/', callback, name='callback'),
    path('stats/', stats, name='stats'),
    path('active_rentals/', active_rentals, name='active_rentals'),
    path('past_rentals/', past_rentals, name='past_rentals'),
    path('cancel_rental/',  cancel_rental, name='cancel_rental'),
    path('admin_stats/',  admin_stats, name='admin_stats'),
    path('rentals/',  rentals, name='rentals'),
    path('report_generation_data/',  report_generation_data, name='report_generation_data'),

    
   
]
