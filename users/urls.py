from django.urls import path
from .views import signup, login, google_login, password_reset, index,update_contact,get_authenticated_user

urlpatterns = [
    path('', index),
    path('signup/', signup),
    path('login/', login),
    path('google_login/', google_login),
    path('password_reset/', password_reset),
    path('user/update-contact/', update_contact),
    path('user/', get_authenticated_user),
    
]
