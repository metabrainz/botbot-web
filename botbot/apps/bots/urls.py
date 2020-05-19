from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^manage/$', views.ManageChannel.as_view(), name='manage_channel'),
    url(r'^delete/$', views.DeleteChannel.as_view(), name='delete_channel'),
]
