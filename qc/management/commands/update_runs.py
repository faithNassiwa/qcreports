from django.core.management import BaseCommand
from qc.models import Run, Contact, Flow


class Command(BaseCommand):
    def handle(self, *args, **options):
        added = 0
        contacts = Contact.objects.all()
        for c in contacts:
            added = Run.add_runs(contact=c)

        self.stdout.write(self.style.SUCCESS('Successfully added %d runs' % added))
