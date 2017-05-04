from django.contrib import admin
from .models import Contact, Message, Group, Email
# Register your models here.
admin.site.register(Contact)
admin.site.register(Message)
admin.site.register(Group)
admin.site.register(Email)
