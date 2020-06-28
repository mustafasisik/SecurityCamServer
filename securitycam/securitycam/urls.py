from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework.authtoken.views import obtain_auth_token  # <-- Here
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('api/login', obtain_auth_token, name='login_api'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)