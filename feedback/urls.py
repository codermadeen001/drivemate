"""# urls.py
from django.urls import path
from .views import submit_feedback, client_get_feedback,delete_feedback ,get_feedback

urlpatterns = [
    path('post/', submit_feedback, name='submit_feedback'),
    path('client_get_feedback/',client_get_feedback, name='client_get_feedback'),
    path('get/', get_feedback, name='get_feedback'),
    path('delete/', delete_feedback, name='delete_feedback'),
  
]

"""


# urls.py
from django.urls import path
from .views import (
    submit_feedback,
    client_get_feedback,
    delete_feedback,
    retrieve_feedback,
)

urlpatterns = [
    path('post/', submit_feedback, name='submit_feedback'),
    path('client_get_feedback/', client_get_feedback, name='client_get_feedback'),
    #path('', get_feedback, name='get_feedback'),
    path('delete/', delete_feedback, name='delete_feedback'),
    path('retrieve_feedback/', retrieve_feedback, name='retrieve_feedback'),
    
]


