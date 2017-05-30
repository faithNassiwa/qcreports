from django.db import models
from django.conf import settings
from temba_client.v2 import TembaClient
from django.core.mail import EmailMessage
import datetime
from django.utils import timezone
import pytz

tz = 'Africa/Kampala'
client = TembaClient(settings.HOST, settings.KEY)


# timezone.make_aware(my_datetime, timezone.get_current_timezone())
# pytz.timezone(tz).localize(models.DateTimeField())


class Flow(models.Model):
    uuid = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    expires = models.IntegerField()
    created_on = models.DateTimeField()
    sync_flows = models.BooleanField(default=False)

    @classmethod
    def add_flows(cls):
        flows = client.get_flows().all()
        added = 0
        # contacts = Contact.objects.filter(sync_flows=False).all()
        for flow in flows:
            if cls.flow_exists(flow):
                cls.objects.filter(uuid=flow.uuid).update(name=flow.name, expires=flow.expires,
                                                          created_on=flow.created_on)
                added += 0
            else:
                cls.objects.create(uuid=flow.uuid, name=flow.name, expires=flow.expires, created_on=flow.created_on)
                added += 1
                # flow = Flow.objects.get(uuid=flow.uuid)

                # for contact in contacts:
                # Run.add_runs(flow=flow, contact=contact)
                # Contact.objects.filter(uuid=contact.uuid).update(sync_flows=True)

        return added

    @classmethod
    def flow_exists(cls, flow):
        return cls.objects.filter(uuid=flow.uuid).exists()

    def __unicode__(self):
        return self.name


class Group(models.Model):
    uuid = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    query = models.CharField(max_length=200, null=True, blank=True)
    count = models.IntegerField()
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)
    get_sync = models.BooleanField(default=False)
    send_sync = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @classmethod
    def add_groups(cls):
        added = 0
        for group_batch in client.get_groups().iterfetches(retry_on_rate_exceed=True):
            for group in group_batch:
                if cls.group_exists(group):
                    cls.objects.filter(uuid=group.uuid).update(name=group.name, query=group.query, count=group.count)
                    added += 0

                else:
                    cls.objects.create(uuid=group.uuid, name=group.name, query=group.query, count=group.count)
                    added += 1
            Flow.add_flows()
        return added

    @classmethod
    def get_group(cls):
        if cls.objects.filter(get_sync=True, count__gte=1).exists():
            groups = cls.objects.filter(get_sync=True, count__gte=1).all()
            for group in groups:
                Contact.save_contacts(group=group)
                Contact.clean_contacts()
        else:
            print ("All groups synced")

    @classmethod
    def group_exists(cls, group):
        return cls.objects.filter(uuid=group.uuid).exists()

    @classmethod
    def get_sms_maama_groups(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(name__in=['SMS Maama 10', 'SMS Maama 11', 'SMS Maama 12', 'SMS Maama 13',
                                            'SMS Maama 14', 'SMS Maama 15', 'SMS Maama 16', 'SMS Maama 17',
                                            'SMS Maama 18', 'SMS Maama 19', 'SMS Maama 20', 'SMS Maama 21',
                                            'SMS Maama 22', 'SMS Maama 23', 'SMS Maama 24', 'SMS Maama 25',
                                            'SMS Maama 26', 'SMS Maama 27', 'SMS Maama 28'],
                                  modified_at__range=(date_diff, datetime.datetime.now())).order_by('name').all()


class Contact(models.Model):
    id = models.IntegerField(primary_key=True)
    uuid = models.CharField(max_length=200)
    name = models.CharField(max_length=200, null=True)
    language = models.CharField(max_length=200, null=True)
    urns = models.CharField(max_length=200)
    groups = models.ForeignKey(Group)
    fields = models.CharField(max_length=200, null=True, blank=True)
    blocked = models.BooleanField(default=False)
    stopped = models.BooleanField(default=False)
    created_on = models.DateTimeField(null=True)
    modified_on = models.DateTimeField(null=True)
    sync_flows = models.BooleanField(default=False)

    @classmethod
    def save_contacts(cls, group):
        added = 0
        folders = ['sent', 'failed', 'flows', 'outbox']
        flows = Flow.objects.filter(sync_flows=True).all()
        for contact_batch in client.get_contacts(group=group.name).iterfetches(retry_on_rate_exceed=True):
            for contact in contact_batch:
                if cls.contact_exists(contact):
                    cls.objects.filter(uuid=contact.uuid).update(name=contact.name, language=contact.language,
                                                                 urns=contact.urns, groups=group,
                                                                 fields=contact.fields.get('points'),
                                                                 blocked=contact.blocked, stopped=contact.stopped,
                                                                 created_on=contact.created_on,
                                                                 modified_on=contact.modified_on)

                else:
                    cls.objects.create(uuid=contact.uuid, name=contact.name, language=contact.language,
                                       urns=contact.urns, groups=group, fields=contact.fields['points'],
                                       blocked=contact.blocked, stopped=contact.stopped,
                                       created_on=contact.created_on, modified_on=contact.modified_on)
                    added += 1

                c = Contact.objects.get(uuid=contact.uuid)

                for folder in folders:
                    Message.save_messages(contact=c, msg_folder=folder)
                    Message.clean_msg_contacts()
                    for f in flows:
                        Run.add_runs(flow=f, contact=c)
                        Flow.objects.filter(uuid=f.uuid).update(sync_flows=False)
                        Contact.objects.filter(uuid=c.uuid).update(sync_flows=True)

            Group.objects.filter(name=group.name).update(get_sync=False)
        return added

    @classmethod
    def contact_exists(cls, contact):
        return cls.objects.filter(uuid=contact.uuid).exists()

    @classmethod
    def get_contacts(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(created_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_contacts_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(created_on__range=(date_diff, datetime.datetime.now())).count()

    # @classmethod
    # def get_sms_maama_contacts(project_list, cls):
    #     return cls.objects.filter(groups__name__in=project_list).all()

    @classmethod
    def get_sms_maama_contacts(cls):
        return cls.objects.filter(groups__name__in=['Baby', 'SMS Maama']).all()

    @classmethod
    def get_sms_maama_contacts_count(cls):
        return cls.objects.filter(groups__name__in=['Baby', 'SMS Maama']).count()

    @classmethod
    def get_sms_maama_weekly_contacts(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(groups__name__in=['Baby', 'SMS Maama'],
                                  created_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_weekly_contacts_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(groups__name__in=['Baby', 'SMS Maama'],
                                  created_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def clean_contacts(cls):
        contacts = cls.objects.all()
        for contact in contacts:
            if 'tel:' in contact.urns:
                cleaned = contact.urns[7:-2]
                cls.objects.filter(uuid=contact.uuid).update(urns=cleaned)

    def __str__(self):
        return str(self.urns)


class Message(models.Model):
    id = models.IntegerField(primary_key=True)
    folder = models.CharField(max_length=200, null=True)
    broadcast = models.IntegerField(null=True)
    contact = models.ForeignKey(Contact)
    urn = models.CharField(max_length=200)
    channel = models.CharField(max_length=200)
    direction = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    status = models.CharField(max_length=200)
    visibility = models.CharField(max_length=200)
    text = models.CharField(max_length=1000)
    labels = models.CharField(max_length=200)
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
    sent_on = models.DateTimeField(null=True, blank=True)
    modified_on = models.DateTimeField(null=True, blank=True)

    @classmethod
    def save_messages(cls, contact, msg_folder):
        added = 0

        for message_batch in client.get_messages(contact=contact.uuid).iterfetches(retry_on_rate_exceed=True):
            for message in message_batch:
                if not cls.message_exists(message):
                    cls.objects.create(id=message.id, folder=msg_folder, broadcast=message.broadcast, contact=contact,
                                       urn=message.urn, channel=message.channel, direction=message.direction,
                                       type=message.type, status=message.status, visibility=message.visibility,
                                       text=message.text, labels=message.labels, created_on=message.created_on,
                                       sent_on=message.sent_on, modified_on=message.modified_on)
                    added += 1
                else:
                    cls.objects.filter(id=message.id).update(folder=msg_folder, broadcast=message.broadcast,
                                                             contact=contact,
                                                             urn=message.urn, channel=message.channel,
                                                             direction=message.direction,
                                                             type=message.type, status=message.status,
                                                             visibility=message.visibility,
                                                             text=message.text, labels=message.labels,
                                                             created_on=message.created_on,
                                                             sent_on=message.sent_on, modified_on=message.modified_on)

        return added

    @classmethod
    def message_exists(cls, message):
        return cls.objects.filter(id=message.id).exists()

    @classmethod
    def get_sent_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_delivered_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', status='delivered',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_failed_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', sent_on__range=(date_diff, datetime.datetime.now())).all() \
            .exclude(status='delivered').all()

    @classmethod
    def sent_messages_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def count_read_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(status='delivered', direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def count_unread_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', sent_on__range=(date_diff, datetime.datetime.now())) \
            .exclude(status='delivered').count()

    @classmethod
    def get_unread_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', status='errored',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_failed_messages_daily(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', status='sent',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_sent_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_sent_messages_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_delivered_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out', status='delivered',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_read_messages_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], status='delivered', direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_failed_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], status='failed', direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_failed_messages_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], status='failed', direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_unread_messages_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).exclude(status='delivered') \
            .count()

    @classmethod
    def get_sms_maama_unread_messages(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out', status='errored',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_weekly_flow_responses(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  created_on__range=(date_diff, datetime.datetime.now())).all()


    @classmethod
    def get_sms_maama_flow_responses(cls):
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  text__in=['yes', 'Yes', 'YES','yee','Yee','y','No', 'NO','no', 'Nedda', 'nedda','n']).all()

    @classmethod
    def get_sms_maama_flow_responses_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  created_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_flow_responses_baby(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  text='Baby', sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_flow_responses_enrollment(cls):
        # date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  text__in=[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
                                            28]).all()

    @classmethod
    def get_sms_maama_flow_responses_baby_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  text='Baby', sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_opted_out(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['SMS Maama Opted Out'], direction='in', status='handled',
                                  text__iexact='STOP', sent_on__range=(date_diff, datetime.datetime.now())).distinct()

    @classmethod
    def get_sms_maama_opted_out_count(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name='SMS Maama Opted Out', direction='in', status='handled',
                                  text__iexact='STOP', sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def clean_msg_contacts(cls):
        msgs = cls.objects.all()
        for msg in msgs:
            if 'tel:' in msg.urn:
                cleaned = msg.urn[4:]
                cls.objects.filter(id=msg.id).update(urn=cleaned)

    def __str__(self):
        return str(self.urn)


class Run(models.Model):
    run_id = models.IntegerField()
    responded = models.BooleanField(default=False)
    contact = models.ForeignKey(Contact)
    flow = models.ForeignKey(Flow)
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()
    exit_type = models.CharField(max_length=100, null=True, blank=True)

    @classmethod
    def add_runs(cls, flow, contact):
        added = 0
        for run_batch in client.get_runs(contact=contact.uuid).iterfetches(retry_on_rate_exceed=True):
            for run in run_batch:
                if cls.run_exists(run):
                    cls.objects.filter(run_id=run.id).update(responded=run.responded, contact=contact,
                                                             created_on=run.created_on, modified_on=run.modified_on,
                                                             exit_type=run.exit_type, flow=flow)
                    r = Run.objects.get(run_id=run.id)
                    Step.add_steps(run=r, steps=run.path)
                    Value.add_values(run=r, values=run.values)
                    added += 0

                else:
                    cls.objects.create(run_id=run.id, responded=run.responded, contact=contact,
                                       created_on=run.created_on, modified_on=run.modified_on,
                                       exit_type=run.exit_type, flow=flow)
                    r = Run.objects.get(run_id=run.id)
                    Step.add_steps(run=r, steps=run.path)
                    Value.add_values(run=r, values=run.values)
                    added += 1

        return added

    @classmethod
    def run_exists(cls, run):
        return cls.objects.filter(run_id=run.id).exists()

    @classmethod
    def sms_maama_contact_flows(cls):
        # date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(responded=True,
                                  flow__name__in=['Screening 1', 'Screening 2', 'Screening 3', 'Screening 4',
                                                  'Screening 5', 'Screening 6', 'Screening 7', 'Screening 8',
                                                  'Screening 9', 'Screening 10', 'Screening 11', 'Screening 12',
                                                  'Screening 13', 'Screening 14', 'Screening 15', 'Screening 16',
                                                  'Screening 17', 'Screening 18', 'Screening 19']).distinct()

    @classmethod
    def sms_maama_contact_flows_antenatal(cls):
        # date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(responded=True,
                                  flow__name__in=['First appointment reminder', 'Second appointment reminder',
                                                  'Third appointment reminder']).distinct()

    def __unicode__(self):
        return str(self.run_id)


class Step(models.Model):
    node = models.CharField(max_length=100)
    time = models.DateTimeField()
    run = models.ForeignKey(Run, on_delete=models.CASCADE)

    @classmethod
    def add_steps(cls, run, steps):
        added = 0
        for step in steps:
            if not cls.step_exists(step):
                cls.objects.create(node=step.node, time=step.time, run=run)
                added += 1
        return added

    @classmethod
    def step_exists(cls, step):
        return cls.objects.filter(node=step.node).exists()

    def __unicode__(self):
        return self.node


class Value(models.Model):
    value = models.CharField(max_length=100, blank=True)
    run = models.ForeignKey(Run, on_delete=models.CASCADE)

    @classmethod
    def add_values(cls, run, values):
        added = 0
        for val in values:
            cls.objects.create(value=val, run=run)
            added += 1
        return added

    @classmethod
    def sms_maama_contact_flows_values(cls):
        # date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(run__responded=True, value__in=['bleeding_with_pain', 'mosquito net response',
                                                                  'due to TB', 'Received Malaria Medicine',
                                                                  'easy before', 'easy before pregnancy',
                                                                  'Pain Urinating', 'increased thirst urination',
                                                                  'foul smell or pain response', 'Reduced Abdomen',
                                                                  'Swelling of your body', 'contractions response',
                                                                  'Headache', 'Delivered', 'Bleeding Response',
                                                                  'signs of infection', 'Baby Yellow Eyes',
                                                                  'Do you feel sad', 'Pap Test'],
                                  run__flow__name__in=['Screening 1', 'Screening 2', 'Screening 3', 'Screening 4',
                                                       'Screening 5', 'Screening 6', 'Screening 7', 'Screening 8',
                                                       'Screening 9', 'Screening 10', 'Screening 11', 'Screening 12',
                                                       'Screening 13', 'Screening 14', 'Screening 15', 'Screening 16',
                                                       'Screening 17', 'Screening 18', 'Screening 19']).distinct()

    @classmethod
    def sms_maama_contact_flows_antenatal_values(cls):
        # date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(run__responded=True, value__in=['4th antenatal appt', '3rd antenatal appt',
                                                                  'attend last antenatal visit'],
                                  run__flow__name__in=['First appointment reminder', 'Second appointment reminder',
                                                       'Third appointment reminder']).distinct()

    def __unicode__(self):
        return self.value


class Email(models.Model):
    name = models.CharField(max_length=100)
    address = models.EmailField(max_length=200)
    project = models.ForeignKey(Group)

    def __str__(self):
        return self.name

    @classmethod
    def add_email(cls, name, address):
        return cls.objects.create(name=name, address=address)

    @classmethod
    def send_message_email(cls, file_name):
        mailing_list = []
        emails = cls.objects.all()
        for email in emails:
            mailing_list.append(email.address)

        email_html_file = '<h4>Please see attached pdf report file</h4>'
        msg = EmailMessage('mCRAG weekly report', email_html_file, settings.EMAIL_HOST_USER, mailing_list)
        msg.attach_file(file_name)
        msg.content_subtype = "html"
        return msg.send()
