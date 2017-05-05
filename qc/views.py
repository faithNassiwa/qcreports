from django.shortcuts import render
from models import Contact, Message
from django.template.loader import render_to_string
from django.utils.timezone import now
from weasyprint import HTML
import datetime


def index(request):
    contacts = Contact.get_contacts()
    sent_messages = Message.get_sent_messages()
    delivered_messages = Message.get_delivered_messages()
    failed_messages = Message.get_failed_messages()
    contacts_count = Contact.get_contacts_count()
    messages_count = Message.sent_messages_count()
    read_messages_count = Message.count_read_messages()
    unread_messages_count = Message.count_unread_messages()
    unread_messages = Message.get_unread_messages()
    this_day = now()
    target = str(this_day)[:-22]
    return render(request, 'index.html', locals())


def daily_messages_failed(request):
    failed_messages_daily = Message.get_failed_messages_daily()
    this_day = now()
    sent_on_date = (datetime.datetime.now()-datetime.timedelta(days=2))
    return render(request, 'failed_messages.html', locals())


def html_to_pdf_view():
    contacts = Contact.get_contacts()
    sent_messages = Message.get_sent_messages()
    contacts_count = Contact.get_contacts_count()
    messages_count = Message.sent_messages_count()
    this_day = now()
    target = str(this_day)[:-22]

    html_string = render_to_string('index.html', {'contacts': contacts, 'sent_messages': sent_messages,
                                                  'this_day': this_day, 'messages_count': messages_count,
                                                  'contacts_count': contacts_count})

    html = HTML(string=html_string)
    html.write_pdf(target='media/'+target+'.pdf')
