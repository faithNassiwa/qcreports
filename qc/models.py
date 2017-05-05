from django.db import models
from django.conf import settings
from temba_client.v2 import TembaClient
from django.core.mail import send_mail, EmailMessage
import datetime


# Create your models here.

class Group(models.Model):
    uuid = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    query = models.CharField(max_length=200, null=True)
    count = models.IntegerField()

    def __str__(self):
        return self.name

    @classmethod
    def add_groups(cls):
        client = TembaClient(settings.HOST, settings.KEY)
        added = 0
        for group_batch in client.get_groups().iterfetches(retry_on_rate_exceed=True):
            for group in group_batch:
                if not cls.group_exists(group):
                    g = cls.objects.create(uuid=group.uuid, name=group.name, query=group.query, count=group.count)
                    Contact.save_contacts(group=g)
                    added += 1
        return added

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
    fields = models.CharField(max_length=200)
    blocked = models.BooleanField(default=False)
    stopped = models.BooleanField(default=False)
    created_on = models.DateTimeField(null=True)
    modified_on = models.DateTimeField(null=True)

    def __str__(self):
        return self.urns

    @classmethod
    def save_contacts(cls, group):
        client = TembaClient(settings.HOST, settings.KEY)
        added = 0
        folders = ['inbox', 'sent', 'flows', 'archived', 'outbox', 'incoming', 'failed', 'calls']

        for contact_batch in client.get_contacts().iterfetches(retry_on_rate_exceed=True):
            for contact in contact_batch:
                if not cls.contact_exists(contact):
                    cls.objects.create(uuid=contact.uuid, name=contact.name, language=contact.language,
                                       urns=contact.urns, groups=group, fields=contact.fields,
                                       blocked=contact.blocked, stopped=contact.stopped,
                                       created_on=contact.created_on, modified_on=contact.modified_on)
                    c = Contact.objects.get(uuid=contact.uuid)

                    for folder in folders:
                        Message.save_messages(contact=c, msg_folder=folder)
                    added += 1
        return added

    @classmethod
    def contact_exists(cls, contact):
        return cls.objects.filter(uuid=contact.uuid).exists()

    @classmethod
    def get_contacts(cls):
        return cls.objects.filter(created_on__gte=datetime.date(2017, 4, 25))

    @classmethod
    def get_contacts_count(cls):
        return cls.objects.filter(created_on__gte=datetime.date(2017, 4, 25)).count()

    @classmethod
    def clean_contacts(cls):
        contacts = cls.objects.all()
        for contact in contacts:
            if 'tel:' in contact.urns:
                cleaned = contact.urns[7:-2]
                cls.objects.filter(uuid=contact.uuid).update(urns=cleaned)


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

    def __str__(self):
        return str(self.urn)

    @classmethod
    def save_messages(cls, contact, msg_folder='sent'):
        client = TembaClient(settings.HOST, settings.KEY)
        added = 0

        for message_batch in client.get_messages(folder=msg_folder).iterfetches(retry_on_rate_exceed=True):
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
        return cls.objects.filter(direction='out', sent_on__gte=datetime.date(2017, 4, 25)).all()

    @classmethod
    def get_delivered_messages(cls):
        return cls.objects.filter(direction='out', status='delivered', sent_on__gte=datetime.date(2017, 4, 25)).all()

    @classmethod
    def get_failed_messages(cls):
        return cls.objects.filter(direction='out', sent_on__gte=datetime.date(2017, 4, 25)).all()\
            .exclude(status='delivered').all()

    @classmethod
    def sent_messages_count(cls):
        return cls.objects.filter(direction='out', sent_on__gte=datetime.date(2017, 4, 25)).count()

    @classmethod
    def count_read_messages(cls):
        return cls.objects.filter(status='delivered', direction='out', sent_on__gte=datetime.date(2017, 4, 25)).count()

    @classmethod
    def count_unread_messages(cls):
        return cls.objects.filter(direction='out', sent_on__gte=datetime.date(2017, 4, 25)).exclude(status='delivered')\
            .count()

    @classmethod
    def get_unread_messages(cls):
        return cls.objects.filter(direction='out', status='errored', sent_on__gte=datetime.date(2017, 4, 25)).all()

    @classmethod
    def get_failed_messages_daily(cls):
        date_diff = datetime.datetime.now() - datetime.timedelta(days=2)
        return cls.objects.filter(direction='out', status='sent', sent_on__range=(date_diff, datetime.datetime.now()))\
            .all()

    @classmethod
    def clean_msg_contacts(cls):
        msgs = cls.objects.all()
        for msg in msgs:
            if 'tel:' in msg.urn:
                cleaned = msg.urn[4:]
                cls.objects.filter(id=msg.id).update(urn=cleaned)


class Email(models.Model):
    name = models.CharField(max_length=100)
    address = models.EmailField(max_length=200)

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
