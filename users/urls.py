# authentication/urls.py

from dj_rest_auth.jwt_auth import get_refresh_view
from users.views.register import CustomRegisterView, CustomLoginView
from dj_rest_auth.views import LoginView, LogoutView, UserDetailsView
from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    path("register/", CustomRegisterView.as_view(), name="custom_register"),
    path("login/", CustomLoginView.as_view(), name="rest_login"),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("user/", UserDetailsView.as_view(), name="rest_user_details"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/refresh/", get_refresh_view().as_view(), name="token_refresh"),
]