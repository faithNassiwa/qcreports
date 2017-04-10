from django.core.management import BaseCommand
from qc.models import Message


class Command(BaseCommand):
    def handle(self, *args, **options):
        folders = ['Inbox', 'Sent', 'Flows', 'Archived', 'Outbox', 'Incoming', 'Failed', 'Calls']
        for folder in folders:
            added = Message.save_messages(folder)
            self.stdout.write(self.style.SUCCESS('Successfully added %d %s messages' % (added, folder)))
