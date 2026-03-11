"""
core URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Including the Lilian AI inventory api routes
    path('api/ai/', include('pol_ai.urls')),
]
