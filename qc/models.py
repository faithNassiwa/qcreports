from django.db import models
from django.conf import settings
from temba_client.v2 import TembaClient
from django.core.mail import EmailMessage
import datetime

client = TembaClient(settings.HOST, settings.KEY)


class Group(models.Model):
    uuid = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    query = models.CharField(max_length=200, null=True, blank=True)
    count = models.IntegerField()
    get_sync = models.BooleanField(default=False)
    send_sync = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @classmethod
    def add_groups(cls):
        added = 0
        for group_batch in client.get_groups().iterfetches(retry_on_rate_exceed=True):
            for group in group_batch:
                if not cls.group_exists(group):
                    cls.objects.create(uuid=group.uuid, name=group.name, query=group.query, count=group.count)
                    added += 1
                elif cls.group_exists(group):
                    cls.objects.filter(uuid=group.uuid).update(name=group.name, query=group.query, count=group.count)
                else:
                    added += 0
        return added

    @classmethod
    def get_group(cls):
        if cls.objects.filter(get_sync=True).exists():
            group = cls.objects.filter(get_sync=True).first()
            Contact.save_contacts(group=group)
            Contact.clean_contacts()
        else:
            print ("All groups synced")

    @classmethod
    def group_exists(cls, group):
        return cls.objects.filter(uuid=group.uuid).exists()


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

    @classmethod
    def save_contacts(cls, group):
        added = 0
        folders = ['sent', 'failed', 'flows', 'outbox']
        for contact_batch in client.get_contacts(group=group.name).iterfetches(retry_on_rate_exceed=True):
            for contact in contact_batch:
                if not cls.contact_exists(contact):
                    cls.objects.create(uuid=contact.uuid, name=contact.name, language=contact.language,
                                       urns=contact.urns, groups=group, fields=contact.fields['points'],
                                       blocked=contact.blocked, stopped=contact.stopped,
                                       created_on=contact.created_on, modified_on=contact.modified_on)
                    added += 1

                else:
                    cls.objects.filter(uuid=contact.uuid).update(name=contact.name, language=contact.language,
                                                                 urns=contact.urns, groups=group,
                                                                 fields=contact.fields.get('points'),
                                                                 blocked=contact.blocked, stopped=contact.stopped,
                                                                 created_on=contact.created_on,
                                                                 modified_on=contact.modified_on)
                c = Contact.objects.get(uuid=contact.uuid)

                for folder in folders:
                    Message.save_messages(contact=c, msg_folder=folder)
                    Message.clean_msg_contacts()
                    Run.add_runs(contact=c)

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
    sent_on = models.DateTimeField(null=True)
    modified_on = models.DateTimeField(null=True)

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
    def get_sms_maama_flow_responses(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  created_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_flow_responses_baby(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  text='Baby', created_on__range=(date_diff, datetime.datetime.now())).all()

    # def get_specific_flow_response(self):
    #
    #     run_flow = Flow.objects.filter(run_id__contact__groups__name__in=['Baby', 'SMS Maama']).all()
    # #run_values = Value.objects.all()
    # run_contact = Run.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama']).all()
    # messages = Message.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], folder='flow').all()
    # # responses = messages.intersection(run_contact, run_flow)
    # result_list = list(chain(run_contact, messages, run_flow))
    #
    #     return messages.union(run_values, run_contact)

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
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()
    exit_type = models.CharField(max_length=100, null=True, blank=True)

    @classmethod
    def add_runs(cls, contact):
        runs = client.get_runs(contact=contact.uuid).all()
        added = 0
        for run in runs:
            if not cls.run_exists(run):
                cls.objects.create(run_id=run.id, responded=run.responded, contact=contact, created_on=run.created_on,
                                   modified_on=run.modified_on, exit_type=run.exit_type)
                r = Run.objects.get(run_id=run.id)
                Step.add_steps(run=r, steps=run.path)
                Value.add_values(run=r, values=run.values)
                Flow.add_flows(run=r, flow=run.flow)
                added += 1

        return added

    @classmethod
    def run_exists(cls, run):
        return cls.objects.filter(run_id=run.id).exists()

    def __unicode__(self):
        return str(self.run_id)


class Step(models.Model):
    node = models.CharField(max_length=100)
    time = models.DateTimeField()
    run_id = models.ForeignKey(Run, on_delete=models.CASCADE)

    @classmethod
    def add_steps(cls, run, steps):
        added = 0
        for step in steps:
            if not cls.step_exists(step):
                cls.objects.create(node=step.node, time=step.time, run_id=run)
                added += 1
        return added

    @classmethod
    def step_exists(cls, step):
        return cls.objects.filter(node=step.node).exists()

    def __unicode__(self):
        return self.node


class Value(models.Model):
    value = models.CharField(max_length=100, blank=True)
    run_id = models.ForeignKey(Run, on_delete=models.CASCADE)

    @classmethod
    def add_values(cls, run, values):
        added = 0
        for val in values:
            cls.objects.create(value=val, run_id=run)
            added += 1
        return added

    def __unicode__(self):
        return self.value


class Flow(models.Model):
    uuid = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    run_id = models.ForeignKey(Run, on_delete=models.CASCADE)

    @classmethod
    def add_flows(cls, run, flow):
        added = 0
        if not cls.flow_exists(flow):
            cls.objects.create(uuid=flow.uuid, name=flow.name, run_id=run)
            added += 1
        return added

    @classmethod
    def flow_exists(cls, flow):
        return cls.objects.filter(uuid=flow.uuid).exists()

    def __unicode__(self):
        return self.name


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
