from django.shortcuts import render
from models import Contact, Message, Run, Flow, Value,Group
from django.template.loader import render_to_string
from django.utils.timezone import now
from weasyprint import HTML
import datetime
from itertools import chain


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


def sms_maama_weekly(request):
    # report_groups = Group.objects.filter(send_sync=True)
    # project_list = []
    # for report_group in report_groups:
    #     project_list.append(report_group.name)

    contacts = Contact.get_sms_maama_weekly_contacts()
    sms_maama_contacts = Contact.get_sms_maama_contacts()
    #sms_maama_contacts = Contact.get_sms_maama_contacts(project_list)
    sent_messages = Message.get_sms_maama_sent_messages()
    delivered_messages = Message.get_sms_maama_delivered_messages()
    failed_messages = Message.get_sms_maama_failed_messages()
    failed_messages_count = Message.get_sms_maama_failed_messages_count()
    contacts_count = Contact.get_sms_maama_contacts_count()
    weekly_contacts_count = Contact.get_sms_maama_weekly_contacts_count()
    messages_count = Message.get_sms_maama_sent_messages_count()
    read_messages_count = Message.get_sms_maama_read_messages_count()
    unread_messages_count = Message.get_sms_maama_unread_messages_count()
    unread_messages = Message.get_sms_maama_unread_messages()
    flow_responses = Message.get_sms_maama_flow_responses()
    baby_responses = Message.get_sms_maama_flow_responses_baby()
    start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    end_date = datetime.datetime.now()
    this_day = now()
    target = str(this_day)[:-22]
    return render(request, 'qcreports/sms_maama_weekly_report.html', locals())


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
