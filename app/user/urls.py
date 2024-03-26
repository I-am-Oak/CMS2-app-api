"""
URL mappings for user API
"""
from django.urls import path
from .views import create_user
from user import views

# urls.py

app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create_user'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),

]
