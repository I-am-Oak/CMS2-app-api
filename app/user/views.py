"""
Views fo the user API.
"""
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)


# Create your views here.
class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """retreve and return the authenticated user"""
        return self.request.user

from django.shortcuts import render, redirect

from django.http import JsonResponse

def create_user(request):
    if request.method == 'POST':
        # Extract form data
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')

        # Validate form data (add your validation logic here)

        # Create user or perform other actions
        # Example: Creating a new user
        # user = User.objects.create(email=email, password=password, name=name)

        # Return success response
        return JsonResponse({'message': 'User created successfully'}, status=201)
    else:
        # Handle non-POST requests
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
