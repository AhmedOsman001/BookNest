from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.views import (
    RecommendationModelViewSet,
    UserRecommendationViewSet,
    AdminRecommendationViewSet
)
from .views.manual_trigger_views import trigger_recommendations

router = DefaultRouter()
router.register(r'models', RecommendationModelViewSet)
router.register(r'user-recommendations', UserRecommendationViewSet, basename='user-recommendations')

urlpatterns = [
    path('', include(router.urls)),
    path('trigger-recommendations/', trigger_recommendations, name='trigger-recommendations'),
]