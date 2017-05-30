import os
import StringIO
from xhtml2pdf import pisa  # reads inline css
from qcreports import settings
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from models import Contact, Message, Run, Flow, Value, Group
from django.template.loader import render_to_string
from django.utils.timezone import now
import datetime
from itertools import chain
from django.views.generic.base import View
from weasyprint import HTML  # no css comes with pdf
from wkhtmltopdf.views import PDFTemplateResponse  # no css comes with pdf
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import letter, cm, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pytz
from django.utils.timezone import localtime

tz = 'Africa/Kampala'


# pytz.timezone(tz).localize(models.DateTimeField())


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
    sent_on_date = (datetime.datetime.now() - datetime.timedelta(days=2))
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
    html.write_pdf(target='media/' + target + '.pdf')


def sms_maama_weekly(request, as_pdf=False):
    # report_groups = Group.objects.filter(send_sync=True).all()
    # project_list = []
    # for report_group in report_groups:
    #     project_list.append(report_group.name)
    # sms_maama_contacts = Contact.get_sms_maama_contacts(project_list)

    groups = Group.get_sms_maama_groups()
    contacts = Contact.get_sms_maama_weekly_contacts()
    sms_maama_contacts = Contact.get_sms_maama_contacts()
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
    flow_responses_count = Message.get_sms_maama_flow_responses_count()
    # responses = Message.get_specific_flow_response()
    baby_responses = Message.get_sms_maama_flow_responses_baby()
    baby_responses_count = Message.get_sms_maama_flow_responses_baby_count()
    stops = Message.get_sms_maama_opted_out()
    stops_count = Message.get_sms_maama_opted_out_count()
    enrollments = Message.get_sms_maama_flow_responses_enrollment()
    flows = Value.sms_maama_contact_flows_values()
    antenatal_responses = Value.sms_maama_contact_flows_antenatal_values()
    start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    end_date = datetime.datetime.now()
    this_day = now()
    target = str(this_day)[:-22]
    payload = {'groups': groups, 'contacts': contacts, 'sms_maama_contacts': sms_maama_contacts,
               'sent_messages': sent_messages, 'delivered_messages': delivered_messages,
               'failed_messages': failed_messages, 'failed_messages_count': failed_messages_count,
               'contacts_count': contacts_count, 'weekly_contacts_count': weekly_contacts_count,
               'messages_count': messages_count, 'read_messages_count': read_messages_count,
               'unread_messages_count': unread_messages_count, 'unread_messages': unread_messages,
               'flow_responses': flow_responses, 'flow_responses_count': flow_responses_count,
               'baby_responses': baby_responses, 'baby_responses_count': baby_responses_count,
               'stops': stops, 'stops_count': stops_count, 'flows': flows, 'antenatal_responses': antenatal_responses,
               'enrollments': enrollments, 'start_date': start_date, 'end_date': end_date, 'this_day': this_day}
    if as_pdf:
        return payload
    return render_to_response('qcreports/sms_maama_weekly_report.html', payload, RequestContext(request))
    # return render(request, 'qcreports/sms_maama_weekly_report.html', locals())


def fetch_resources(uri, rel):
    path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    print path
    return path


def generate_pdf(request):
    payload = sms_maama_weekly(request, as_pdf=True)
    file_data = render_to_string('qcreports/sms_maama_weekly_report.html', payload)
    my_file = StringIO.StringIO()
    pisa.CreatePDF(file_data, my_file, link_callback=fetch_resources)
    response = HttpResponse(my_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=sms_maama_weekly_report.pdf'
    return response


def pdf_view(request):
    payload = sms_maama_weekly(request, as_pdf=True)
    file_data = render_to_string('qcreports/sms_maama_weekly_report.html', payload)
    my_file = StringIO.StringIO()
    pisa.CreatePDF(file_data, my_file)
    my_file.seek(0)
    response = HttpResponse(my_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; sms_maama_weekly_report.pdf'
    return response


def sms_maama_report():
    doc = SimpleDocTemplate("qc/static/qc/reports/sms_maama_weekly_report_{end_date}.pdf", pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)

    report = []
    logo = "qc/static/images/logo.jpg"
    project_name = "SMS MAAMA Project"
    report_title = "SMS Maama Weekly Report"
    prepared_by = "TMCG Personnel"
    groups = Group.get_sms_maama_groups()
    contacts = Contact.get_sms_maama_weekly_contacts()
    sms_maama_contacts = Contact.get_sms_maama_contacts()
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
    flow_responses_weekly = Message.get_sms_maama_weekly_flow_responses()
    flow_responses_count = Message.get_sms_maama_flow_responses_count()
    baby_responses = Message.get_sms_maama_flow_responses_baby()
    baby_responses_count = Message.get_sms_maama_flow_responses_baby_count()
    stops = Message.get_sms_maama_opted_out()
    stops_count = Message.get_sms_maama_opted_out_count()
    flows = Value.sms_maama_contact_flows_values()
    antenatal_responses = Value.sms_maama_contact_flows_antenatal_values()
    enrollments = Message.get_sms_maama_flow_responses_enrollment()
    start_date = datetime.date.today() - datetime.timedelta(days=7)
    end_date = datetime.date.today()
    this_day = datetime.datetime.now(pytz.timezone('Africa/Kampala')).strftime('%Y-%m-%d %H:%M %Z')

    im = Image(logo, 4 * inch, inch)
    report.append(im)
    report.append(Spacer(1, 12))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
    ptext = '<font size=14><b>%s</b></font>' % report_title
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    ptext = '<font size=12>Date: %s</font>' % this_day
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    ptext = '<font size=12> Report Date: %s - %s</font>' % (start_date, end_date)
    report.append(Paragraph(ptext, styles["Normal"]))
    ptext = '<font size=12> Prepared By: %s</font>' % prepared_by
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))

    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    ptext = '<font size=12> <b>All SMS Maama Contacts.</b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    all_sms_maama_contact_titles = ['Phone Number', 'Name', 'Points', 'Enrolled On', 'Week Enrolled']
    data = [all_sms_maama_contact_titles]
    colwidths = (100, 100, 60, 120, 80)
    for i, contact in enumerate(sms_maama_contacts):
        for j, enrollment in enumerate(enrollments):
            if contact.urns == enrollment.urn:
                data.append(
                    [contact.urns, contact.name, contact.fields,localtime(contact.created_on).strftime('%Y-%m-%d %H:%M'),
                     enrollment.text])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)
    report.append(Spacer(1, 12))
    report.append(Spacer(1, 12))

    ptext = '<font size=12> <b>SMS Maama Week of Pregnancy Upon Enrollment Status</b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    groups_titles = ['SMS Maama Week', 'Number of Participants']
    data = [groups_titles]
    colwidths = (230, 230)
    for i, group in enumerate(groups):
        data.append([group.name, group.count])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)
    ptext = '<font size=12> <center>Total Participants: %s</center></font>' % contacts_count
    report.append(Paragraph(ptext, styles["Normal"]))

    report.append(Spacer(1, 12))
    report.append(Spacer(1, 12))
    report.append(Spacer(1, 12))
    ptext = '<font size=12> <b> Weekly Enrolled Contacts</b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    contacts_titles = ['Phone Number', 'Enrolled On', 'Language']
    data = [contacts_titles]
    colwidths = (150, 150, 150)
    for i, weekly_contact in enumerate(contacts):
        data.append(
            [weekly_contact.urns, weekly_contact.created_on.strftime("%Y-%m-%d %H:%M"), weekly_contact.language])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)
    ptext = '<font size=12> <center>Total Weekly Participants: %s</center></font>' % weekly_contacts_count
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))

    ptext = '<font size=12> <b> Weekly read messages </b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    read_messages_titles = ['Phone Number', 'Message', 'Status', 'Sent On']
    data = [read_messages_titles]
    colwidths = (100, 160, 100, 100)
    for i, delivered_message in enumerate(delivered_messages):
        data.append(
            [delivered_message.urn, Paragraph(delivered_message.text, styles["BodyText"]), delivered_message.status,
             localtime(delivered_message.sent_on).strftime("%Y-%m-%d %H:%M")])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)
    ptext = '<font size=12> <center>Total Messages Sent: %s</center></font>' % messages_count
    report.append(Paragraph(ptext, styles["Normal"]))
    ptext = '<font size=12> <center>Total Messages Read: %s</center></font>' % read_messages_count
    report.append(Paragraph(ptext, styles["Normal"]))

    report.append(Spacer(1, 12))
    ptext = '<font size=12> <b> Weekly failed to send messages </b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    failed_messages_titles = ['Phone Number', 'Message', 'Status', 'Sent On']
    data = [failed_messages_titles]
    colwidths = (100, 160, 100, 100)
    for i, failed_message in enumerate(failed_messages):
        data.append(
            [failed_message.urn, Paragraph(failed_message.text, styles["BodyText"]), failed_message.status,
             localtime(failed_message.sent_on).strftime('%Y-%m-%d %H:%M')])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)
    ptext = '<font size=12> <center>Total Failed to Send Messages: %s</center></font>' % failed_messages_count
    report.append(Paragraph(ptext, styles["Normal"]))

    report.append(Spacer(1, 12))
    ptext = '<font size=12> <center> Weekly Responses </center></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    flow_responses_titles = ['Phone Number', 'Message', 'Status', 'Sent On']
    data = [flow_responses_titles]
    colwidths = (100, 130, 100, 130)
    for i, flow_response in enumerate(flow_responses_weekly):
        data.append(
            [flow_response.urn, Paragraph(flow_response.text, styles["BodyText"]), flow_response.status,
             localtime(flow_response.sent_on).strftime('%Y-%m-%d %H:%M')])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)
    ptext = '<font size=12> <center>Total Weekly Responses: %s</center></font>' % flow_responses_count
    report.append(Paragraph(ptext, styles["Normal"]))

    report.append(Spacer(1, 12))
    ptext = '<font size=12> <b> Weekly Baby, Post-Partum Initiations </b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    baby_responses_titles = ['Phone Number', 'Message', 'Status', 'Sent On']
    data = [baby_responses_titles]
    colwidths = (100, 130, 100, 130)
    for i, baby_response in enumerate(baby_responses):
        data.append(
            [baby_response.urn, Paragraph(baby_response.text, styles["BodyText"]), baby_response.status,
             localtime(baby_response.sent_on).strftime('%Y-%m-%d %H:%M')])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)
    ptext = '<font size=12> <center>Total Weekly Baby Responses: %s</center></font>' % baby_responses_count
    report.append(Paragraph(ptext, styles["Normal"]))

    report.append(Spacer(1, 12))
    ptext = '<font size=12> <b> Weekly Terminations </b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    stops_titles = ['Phone Number', 'Message', 'Status', 'Sent On']
    data = [stops_titles]
    colwidths = (100, 130, 100, 130)
    for i, stop in enumerate(stops):
        data.append(
            [stop.urn, Paragraph(stop.text, styles["BodyText"]), stop.status,
             localtime(stop.sent_on).strftime('%Y-%m-%d %H:%M')])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)
    ptext = '<font size=12> <center>Total Weekly Terminations: %s</center></font>' % stops_count
    report.append(Paragraph(ptext, styles["Normal"]))

    report.append(Spacer(1, 12))
    report.append(Spacer(1, 12))
    report.append(Spacer(1, 12))
    report.append(Spacer(1, 12))
    report.append(Spacer(1, 12))
    ptext = '<font size=12><b>Responses to Screening Questions</b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    flow_responsess_titles = ['Phone Number', 'Screening', 'Question Sent On', 'Response', 'Sent On']
    data = [flow_responsess_titles]
    colwidths = (100, 100, 100, 60, 100)
    for i, f in enumerate(flows):
        for j, fr in enumerate(flow_responses):
            if f.run.contact.urns == fr.urn:
                data.append([f.run.contact.urns, f.run.flow.name, localtime(f.run.created_on).strftime('%Y-%m-%d %H:%M'),
                             fr.text, localtime(fr.sent_on).strftime('%Y-%m-%d %H:%M')])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)

    report.append(Spacer(1, 12))
    report.append(Spacer(1, 12))
    ptext = '<font size=12><b>Response to Antenatal Reminders</b></font>'
    report.append(Paragraph(ptext, styles["Normal"]))
    report.append(Spacer(1, 12))
    antenatal_responses_titles = ['Phone Number', 'Appointment Reminder', 'Reminder Sent On', 'Response', 'Sent On']
    data = [antenatal_responses_titles]
    colwidths = (80, 120, 100, 60, 100)
    for i, ar in enumerate(antenatal_responses):
        for j, fr in enumerate(flow_responses):
            if ar.run.contact.urns == fr.urn:
                    data.append(
                        [ar.run.contact.urns, ar.run.flow.name, localtime(ar.run.created_on).strftime('%Y-%m-%d %H:%M'),
                         fr.text, localtime(fr.sent_on).strftime('%Y-%m-%d %H:%M')])
    t = Table(data, colwidths, style=[('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                      ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                      ])
    report.append(t)

    doc.build(report)


def print_report(request):
    sms_maama_report()
    pdf = open("qc/static/qc/reports/sms_maama_weekly_report_{end_date}.pdf", "rb").read()
    return HttpResponse(pdf, content_type="application/pdf")


class MyPDFView(View):
    template = 'qcreports/test.html'  # the template
    # report_groups = Group.objects.filter(send_sync=True).all()
    # project_list = []
    # for report_group in report_groups:
    #     project_list.append(report_group.name)
    # sms_maama_contacts = Contact.get_sms_maama_contacts(project_list)
    groups = Group.get_sms_maama_groups()
    contacts = Contact.get_sms_maama_weekly_contacts()
    sms_maama_contacts = Contact.get_sms_maama_contacts()
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
    flow_responses_count = Message.get_sms_maama_flow_responses_count()
    # responses = Message.get_specific_flow_response()
    baby_responses = Message.get_sms_maama_flow_responses_baby()
    baby_responses_count = Message.get_sms_maama_flow_responses_baby_count()
    stops = Message.get_sms_maama_opted_out()
    stops_count = Message.get_sms_maama_opted_out_count()
    flows = Run.sms_maama_contact_flows()
    antenatal_responses = Run.sms_maama_contact_flows_antenatal()
    start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    end_date = datetime.datetime.now()
    this_day = now()
    context = {'groups': groups, 'contacts': contacts, 'sms_maama_contacts': sms_maama_contacts,
               'sent_messages': sent_messages, 'delivered_messages': delivered_messages,
               'failed_messages': failed_messages, 'failed_messages_count': failed_messages_count,
               'contacts_count': contacts_count, 'weekly_contacts_count': weekly_contacts_count,
               'messages_count': messages_count, 'read_messages_count': read_messages_count,
               'unread_messages_count': unread_messages_count, 'unread_messages': unread_messages,
               'flow_responses': flow_responses, 'flow_responses_count': flow_responses_count,
               'baby_responses': baby_responses, 'baby_responses_count': baby_responses_count,
               'stops': stops, 'stops_count': stops_count, 'flows': flows, 'antenatal_responses': antenatal_responses,
               'start_date': start_date, 'end_date': end_date,
               'this_day': this_day}  # data that has to be renderd to pdf templete

    def get(self, request):
        response = PDFTemplateResponse(request=request,
                                       template=self.template,
                                       filename="sms_maama_weekly_report.pdf",
                                       context=self.context,
                                       show_content_in_browser=False,
                                       # cmd_options={'margin-top': 10,
                                       #              "zoom": 1,
                                       #              "viewport-size": "1366 x 513",
                                       #              'javascript-delay': 1000,
                                       #              'footer-center': '[page]/[topage]',
                                       #              "no-stop-slow-scripts": True},
                                       )
        return response


class TestMyPDFView(View):
    template = 'qcreports/test.html'  # the template
    context = {'title': 'Hello World!'}

    def get(self, request):
        response = PDFTemplateResponse(request=request,
                                       template=self.template,
                                       filename="test.pdf",
                                       context=self.context,
                                       show_content_in_browser=False,
                                       )
        return response
