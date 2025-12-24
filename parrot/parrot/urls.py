from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('apps.core.urls')),
    path('', include('apps.library.urls')),
    path('', include('apps.study.urls')),

    path('accounts/', include('django.contrib.auth.urls')),
]
