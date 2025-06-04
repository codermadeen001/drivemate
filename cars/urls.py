from django.urls import path
from .views import (
    create_car,
    get_all_cars,
    car_data,
    maintance,
    delete,
    high_risk_cars  # Ensure the function name in views is correct
)

urlpatterns = [
    path('create/', create_car, name='create_car'),
    path('get_cars/', get_all_cars, name='get_all_cars'),
    path('car_data/', car_data, name='car_data'),
    path('maintance/', maintance, name='maintance'),
    path('high_risk_cars/', high_risk_cars, name='high_risk_cars'),
    path('delete/', delete, name='delete'),
]


