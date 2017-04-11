from django.core.management import BaseCommand
from qc.models import Group, Contact, Message


class Command(BaseCommand):
    def handle(self, *args, **options):
            added = Group.add_groups()
            Contact.clean_contacts()
            Message.clean_msg_contacts()
            self.stdout.write(self.style.SUCCESS('Successfully added %d groups' % added))
