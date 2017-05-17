from django.core.management import BaseCommand
from qc.models import Group


class Command(BaseCommand):
    def handle(self, *args, **options):
            added = Group.add_groups()
            self.stdout.write(self.style.SUCCESS('Successfully added %d groups' % added))
