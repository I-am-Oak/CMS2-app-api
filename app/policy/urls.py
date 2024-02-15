"""
URL mappings for the policy app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from policy import views

router = DefaultRouter()
router.register('policys', views.PolicyViewSet)
router.register('tags', views.TagViewSet)
router.register('claims', views.ClaimViewSet)

app_name = 'policy'

urlpatterns = [
    path('', include(router.urls)),
]
