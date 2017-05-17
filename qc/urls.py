from django.conf.urls import url, include
import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^sms_maama_weekly/$', views.sms_maama_weekly),
    url(r'^failed_messages/$', views.daily_messages_failed),
]
