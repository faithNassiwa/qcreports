from django.conf.urls import url, include
import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^failed_messages/$', views.daily_messages_failed),
]
