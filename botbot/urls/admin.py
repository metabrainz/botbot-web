from django.conf.urls import include
from django.urls import path
from django.contrib import admin


urlpatterns = [
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
]
