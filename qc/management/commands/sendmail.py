from django.core.management import BaseCommand
from qc.views import html_to_pdf_view
from django.utils.timezone import now
from qc.models import Group, Contact, Message, Email


class Command(BaseCommand):
    def handle(self, *args, **options):
        Group.add_groups()
        Contact.clean_contacts()
        Message.clean_msg_contacts()
        html_to_pdf_view()
        this_day = now()
        target = 'media/'+str(this_day)[:-22]+'.pdf'
        Email.send_message_email(target)
        self.stdout.write(self.style.SUCCESS('Successfully sent Email'))
