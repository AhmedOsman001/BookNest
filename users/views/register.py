# users/views.py
from dj_rest_auth.registration.views import RegisterView, LoginView
from users.serializers.auth_serializer import CustomRegisterSerializer, CustomLoginSerializer
from rest_framework.response import Response
from rest_framework import status

class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer

    
class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer