from django.shortcuts import render
from models import Contact, Message
from django.template.loader import render_to_string
from django.utils.timezone import now
from weasyprint import HTML


def index(request):
    contacts = Contact.get_contacts()
    sent_messages = Message.get_sent_messages()
    contacts_count = Contact.get_contacts_count()
    messages_count = Message.sent_messages_count()
    this_day = now()
    target = str(this_day)[:-22]
    return render(request, 'index.html', {'contacts': contacts, 'sent_messages': sent_messages, 'this_day': this_day,
                                          'messages_count': messages_count, 'contacts_count': contacts_count,
                                          'target': target})


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
