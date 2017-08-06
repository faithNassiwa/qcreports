from django.core.management import BaseCommand
from qc.views import html_to_pdf_view
from django.utils.timezone import now
from qc.models import Group, Contact, Message, Run


class Command(BaseCommand):
    def handle(self, *args, **options):
        Group.add_groups()
        Group.objects.filter(name__in=['Baby', 'SMS Maama', 'SMS Maama Opted Out'], count__gte=1).update(get_sync=True)
        Group.get_group()
        # Contact.clean_contacts()
        # Message.clean_msg_contacts()
        self.stdout.write(self.style.SUCCESS('Successfully synced all sms maama groups'))
