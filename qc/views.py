from django.http import HttpResponse
from django.shortcuts import render
from models import Contact, Message


def index(request):
    contacts = Contact.objects.all()
    messages = Message.objects.all()
    return render(request, 'index.html', {'contacts': contacts, 'messages': messages})
