from django.core.management import BaseCommand
from qc.models import Contact


class Command(BaseCommand):
    def handle(self, *args, **options):
        added = Contact.save_contacts()
        self.stdout.write(self.style.SUCCESS('Successfully added %d contacts' % added))
