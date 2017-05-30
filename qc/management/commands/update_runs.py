from django.core.management import BaseCommand
from qc.models import Run, Contact, Flow


class Command(BaseCommand):
    def handle(self, *args, **options):

        flows = Flow.objects.filter(sync_flows=True).all()
        contacts = Contact.objects.filter(sync_flows=True).all()
        for f in flows:
            for c in contacts:

                added = Run.add_runs(flow=f, contact=c)
                Flow.objects.filter(uuid=f.uuid).update(sync_flows=False)
                Contact.objects.filter(uuid=c.uuid).update(sync_flows=False)

        self.stdout.write(self.style.SUCCESS('Successfully added %d runs' % added))
