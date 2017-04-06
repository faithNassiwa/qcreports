from django.core.management import BaseCommand
from qc.models import Message


class Command(BaseCommand):
    def handle(self, *args, **options):
        added = Message.save_messages()
        self.stdout.write(self.style.SUCCESS('Successfully added %d messages' % added))
