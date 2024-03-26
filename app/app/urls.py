from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django_prometheus import urls as prometheus_urls  # Import Django Prometheus URLs

from . import views
from django.contrib import admin
from .views import LoginPageView

urlpatterns = [
    path('', views.page.as_view(), name='index'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('home/', views.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='api_schema'),
    path('api/docs/',
         SpectacularSwaggerView.as_view(url_name='api_schema'),
         name='api-docs'
         ),
    path('api/user/', include('user.urls')),
    path('api/policy/', include('policy.urls')),
    # Add Django Prometheus URL pattern
    path('', include(prometheus_urls)),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
