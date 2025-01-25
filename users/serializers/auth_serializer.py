# users/serializers.py
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from allauth.account.adapter import get_adapter
from django.utils.translation import gettext_lazy as _

class CustomRegisterSerializer(RegisterSerializer):
    # Remove fields we don't want
    first_name = None
    last_name = None
    
    # Define fields we want
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
        }
    
    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def custom_signup(self, request, user):
        pass  # You can add additional signup steps here if needed
    
    


class CustomLoginSerializer(LoginSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        request = self.context.get('request')

        adapter = get_adapter()
        user = adapter.authenticate(request=request ,email=email, password=password)

        if not user:
            msg = _('Unable to log in with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs