from django.db import models
from django.conf import settings
from temba_client.v2 import TembaClient
from django.core.mail import EmailMessage
import datetime
from django.utils import timezone
import pytz

tz = 'Africa/Kampala'
client = TembaClient(settings.HOST, settings.KEY)


class Flow(models.Model):
    uuid = models.CharField(max_length=45)
    name = models.CharField(max_length=100)
    expires = models.IntegerField()
    created_on = models.DateTimeField()
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    @classmethod
    def add_flows(cls):
        flows = client.get_flows().all()
        added = 0
        for flow in flows:
            if cls.flow_exists(flow):
                cls.objects.filter(uuid=flow.uuid).update(name=flow.name, expires=flow.expires,
                                                          created_on=flow.created_on)
                added += 0
            else:
                cls.objects.create(uuid=flow.uuid, name=flow.name, expires=flow.expires, created_on=flow.created_on)
                added += 1

        return added

    @classmethod
    def flow_exists(cls, flow):
        return cls.objects.filter(uuid=flow.uuid).exists()

    def __unicode__(self):
        return self.name


class Group(models.Model):
    uuid = models.CharField(max_length=45)
    name = models.CharField(max_length=100)
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
        return cls.objects.filter(name__in=['SMS Maama 10', 'SMS Maama 11', 'SMS Maama 12', 'SMS Maama 13',
                                            'SMS Maama 14', 'SMS Maama 15', 'SMS Maama 16', 'SMS Maama 17',
                                            'SMS Maama 18', 'SMS Maama 19', 'SMS Maama 20', 'SMS Maama 21',
                                            'SMS Maama 22', 'SMS Maama 23', 'SMS Maama 24', 'SMS Maama 25',
                                            'SMS Maama 26', 'SMS Maama 27', 'SMS Maama 28']).order_by('name').all()


class Contact(models.Model):
    id = models.IntegerField(primary_key=True)
    uuid = models.CharField(max_length=45)
    name = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=50, null=True, blank=True)
    urns = models.CharField(max_length=20)
    groups = models.ForeignKey(Group)
    fields = models.TextField(null=True, blank=True)
    points = models.CharField(max_length=2, null=True, blank=True)
    number_of_weeks = models.CharField(max_length=2, null=True, blank=True)
    blocked = models.BooleanField(default=False)
    stopped = models.BooleanField(default=False)
    created_on = models.DateTimeField(null=True, blank=True)
    modified_on = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    @classmethod
    def save_contacts(cls, group):
        added = 0
        folders = ['sent', 'failed', 'flows', 'outbox']
        for contact_batch in client.get_contacts(group=group.name).iterfetches(retry_on_rate_exceed=True):
            for contact in contact_batch:
                if cls.contact_exists(contact):
                    cls.objects.filter(uuid=contact.uuid).update(name=contact.name, language=contact.language,
                                                                 urns=contact.urns, groups=group, fields=contact.fields,
                                                                 points=contact.fields.get('points'),
                                                                 number_of_weeks=contact.fields.get('number_of_weeks'),
                                                                 blocked=contact.blocked, stopped=contact.stopped,
                                                                 created_on=contact.created_on,
                                                                 modified_on=contact.modified_on)

                else:
                    cls.objects.create(uuid=contact.uuid, name=contact.name, language=contact.language,
                                       urns=contact.urns, groups=group, fields=contact.fields, points=contact.fields['points'],
                                       number_of_weeks=contact.fields['number_of_weeks'],
                                       blocked=contact.blocked, stopped=contact.stopped,
                                       created_on=contact.created_on, modified_on=contact.modified_on)
                    added += 1

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


    @classmethod
    def get_sms_maama_contacts(cls):
        return cls.objects.filter(groups__name__in=['Baby', 'SMS Maama']).all()

    @classmethod
    def get_sms_maama_contacts_count(cls):
        return cls.objects.filter(groups__name__in=['Baby', 'SMS Maama']).count()

    @classmethod
    def get_sms_maama_weekly_contacts(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(groups__name__in=['Baby', 'SMS Maama'],
                                  created_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_weekly_contacts_count(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
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
    folder = models.CharField(max_length=20, null=True)
    broadcast = models.IntegerField(null=True, blank=True)
    contact = models.ForeignKey(Contact)
    urn = models.CharField(max_length=20)
    channel = models.CharField(max_length=200)
    direction = models.CharField(max_length=3)
    type = models.CharField(max_length=10)
    status = models.CharField(max_length=20)
    visibility = models.CharField(max_length=20)
    text = models.TextField()
    labels = models.CharField(max_length=100)
    created_on = models.DateTimeField()
    sent_on = models.DateTimeField(null=True, blank=True)
    modified_on = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)

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
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def count_read_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(status='delivered', direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def count_unread_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', sent_on__range=(date_diff, datetime.datetime.now())) \
            .exclude(status='delivered').count()

    @classmethod
    def get_unread_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', status='errored',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_failed_messages_daily(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(direction='out', status='sent',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_sent_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_sent_messages_count(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_delivered_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out', status='delivered',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_read_messages_count(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], status='delivered', direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_failed_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], status='failed', direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_failed_messages_count(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], status='failed', direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_hanging_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())). \
            exclude(status__in=['delivered', 'failed', 'errored', 'handled']).all()

    @classmethod
    def get_sms_maama_hanging_messages_count(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out',
                                  sent_on__range=(date_diff, datetime.datetime.now())). \
            exclude(status__in=['delivered', 'failed', 'errored', 'handled']).count()

    @classmethod
    def get_sms_maama_unread_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='out', status='errored',
                                  sent_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_weekly_flow_responses(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  created_on__range=(date_diff, datetime.datetime.now())).all()

    @classmethod
    def get_sms_maama_flow_responses_count(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  created_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_flow_responses_baby(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
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
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['Baby', 'SMS Maama'], direction='in', status='handled',
                                  text='Baby', sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def get_sms_maama_opted_out(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name__in=['SMS Maama Opted Out'], direction='in', status='handled',
                                  text__iexact='STOP', sent_on__range=(date_diff, datetime.datetime.now())).distinct()

    @classmethod
    def get_sms_maama_opted_out_count(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(contact__groups__name='SMS Maama Opted Out', direction='in', status='handled',
                                  text__iexact='STOP', sent_on__range=(date_diff, datetime.datetime.now())).count()

    @classmethod
    def clean_msg_contacts(cls):
        msgs = cls.objects.all()
        for msg in msgs:
            if 'tel:' in msg.urn:
                cleaned = msg.urn[4:]
                cls.objects.filter(id=msg.id).update(urn=cleaned)

    @classmethod
    def get_concerning_messages(cls):
        date_diff = datetime.date.today() - datetime.timedelta(days=7)
        return cls.objects.filter(urn='+256779094147', sent_on__range=(date_diff, datetime.datetime.now()))

    @classmethod
    def get_incoming_messages(cls):
        return cls.objects.filter(direction='in').exclude(id__gte=1233332).all()

    @classmethod
    def get_outgoing_messages(cls):
        return cls.objects.filter(direction='out').all()

    @classmethod
    def get_cost_of_incoming_messages(cls, number_of_incoming_messages):
        return number_of_incoming_messages * 70

    @classmethod
    def get_cost_of_outgoing_messages(cls, number_of_outgoing_messages):
        return number_of_outgoing_messages * 25

    def __str__(self):
        return str(self.urn)


class Run(models.Model):
    run_id = models.IntegerField()
    responded = models.BooleanField(default=False)
    contact = models.ForeignKey(Contact)
    flow = models.ForeignKey(Flow, blank=True, null=True)
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()
    exit_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    @classmethod
    def add_runs(cls, contact):
        added = 0
        for run_batch in client.get_runs(contact=contact.uuid).iterfetches(retry_on_rate_exceed=True):
            for run in run_batch:
                if not cls.run_exists(run):
                    cls.objects.create(run_id=run.id, responded=run.responded, contact=contact,
                                       created_on=run.created_on, modified_on=run.modified_on,
                                       exit_type=run.exit_type)

                    r = Run.objects.get(run_id=run.id)
                    flow = Flow.objects.get(uuid=run.flow.uuid)
                    Run.objects.filter(run_id=run.id).update(flow=flow.id)
                    Step.add_steps(run=r, steps=run.path)
                    Value.add_values(run=r, values=run.values)
                    added += 1

                else:
                    cls.objects.filter(run_id=run.id).update(responded=run.responded, contact=contact,
                                                             created_on=run.created_on, modified_on=run.modified_on,
                                                             exit_type=run.exit_type)
                    r = Run.objects.get(run_id=run.id)
                    flow = Flow.objects.get(uuid=run.flow.uuid)
                    Run.objects.filter(run_id=run.id).update(flow=flow.id)
                    Step.add_steps(run=r, steps=run.path)
                    Value.add_values(run=r, values=run.values)

        return added

    @classmethod
    def run_exists(cls, run):
        return cls.objects.filter(run_id=run.id).exists()

    @classmethod
    def sms_maama_contact_flows(cls):
        return cls.objects.filter(responded=True,
                                  flow__name__in=['Screening 1', 'Screening 2', 'Screening 3', 'Screening 4',
                                                  'Screening 5', 'Screening 6', 'Screening 7', 'Screening 8',
                                                  'Screening 9', 'Screening 10', 'Screening 11', 'Screening 12',
                                                  'Screening 13', 'Screening 14', 'Screening 15', 'Screening 16',
                                                  'Screening 17', 'Screening 18', 'Screening 19']).distinct()

    @classmethod
    def sms_maama_contact_flows_antenatal(cls):
        return cls.objects.filter(responded=True,
                                  flow__name__in=['First appointment reminder', 'Second appointment reminder',
                                                  'Third appointment reminder']).distinct()

    def __unicode__(self):
        return str(self.run_id)


class Step(models.Model):
    node = models.CharField(max_length=100)
    time = models.DateTimeField()
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)

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
    value_name = models.CharField(max_length=100, blank=True, null=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    node = models.CharField(max_length=100, blank=True, null=True)
    time = models.DateTimeField(blank=True, null=True)
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __unicode__(self):
        return self.value

    @classmethod
    def add_values(cls, run, values):
        added = 0
        for outer_key, inner_dictionary in values.items():
            if not cls.value_exists(run=run):
                cls.objects.create(value_name=outer_key, value=values[outer_key].value,
                                   category=values[outer_key].category,
                                   node=values[outer_key].node,
                                   time=values[outer_key].time, run=run)
                added += 1
            else:
                cls.objects.filter(run=run).update(value_name=outer_key, value=values[outer_key].value,
                                                   category=values[outer_key].category,
                                                   node=values[outer_key].node,
                                                   time=values[outer_key].time)

        return added

    @classmethod
    def value_exists(cls, run):
        return cls.objects.filter(run=run).exists()

    @classmethod
    def sms_maama_contact_flows_responses(cls):
        return cls.objects.filter(value_name__in=['bleeding_with_pain', 'mosquito_net_response',
                                                  'due_to_tb', 'received_malaria_medicine',
                                                  'easy_before', 'easy_before_pregnancy',
                                                  'pain_urinating', 'increased_thirst_urination',
                                                  'foul_smell_or_pain_response', 'reduced_abdomen',
                                                  'swelling_of_your_body', 'contractions_response',
                                                  'Headache', 'Delivered', 'Bleeding_Response',
                                                  'signs_of_infection', 'baby_yellow_eyes',
                                                  'do_you_feel_sad', 'pap_test', 'baby_move_response',
                                                  '4th_antenatal_appt', '3rd_antenatal_appt',
                                                  'attend_last_antenatal_visit'],
                                  run__responded=True).order_by('run__contact__created_on')
    @classmethod
    def sms_maama_contact_flows_screening_values(cls):
        return cls.objects.filter(value_name__in=['bleeding_with_pain', 'mosquito_net_response',
                                                  'due_to_tb', 'received_malaria_medicine',
                                                  'easy_before', 'easy_before_pregnancy',
                                                  'pain_urinating', 'increased_thirst_urination',
                                                  'foul_smell_or_pain_response', 'reduced_abdomen',
                                                  'swelling_of_your_body', 'contractions_response',
                                                  'Headache', 'Delivered', 'Bleeding_Response',
                                                  'signs_of_infection', 'baby_yellow_eyes',
                                                  'do_you_feel_sad', 'pap_test', 'baby_move_response'],
                                  run__responded=True).order_by('run__contact__created_on')

    @classmethod
    def sms_maama_contact_flows_antenatal_values(cls):
        return cls.objects.filter(run__responded=True, value_name__in=['4th_antenatal_appt', '3rd_antenatal_appt',
                                                                       'attend_last_antenatal_visit']).\
            order_by('run__contact__created_on')


class Email(models.Model):
    name = models.CharField(max_length=100)
    address = models.EmailField(max_length=200)
    project = models.ForeignKey(Group)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False)

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
