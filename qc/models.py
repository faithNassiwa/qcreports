from django.db import models
from django.conf import settings
from temba_client.v2 import TembaClient
from django.core.mail import send_mail, EmailMessage


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
        groups = client.get_groups().all()
        added = 0
        for group in groups:
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
        return self.uuid

    @classmethod
    def save_contacts(cls, group):
        client = TembaClient(settings.HOST, settings.KEY)
        contacts = client.get_contacts().all()
        added = 0
        folders = ['Inbox', 'Sent', 'Flows', 'Archived', 'Outbox', 'Incoming', 'Failed', 'Calls']

        for contact in contacts:
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
        return cls.objects.all()

    @classmethod
    def get_contacts_count(cls):
        return cls.objects.count()

    @classmethod
    def clean_contacts(cls):
        contacts = cls.objects.all()
        for contact in contacts:
            if 'tel:' in contact.urns:
                cleaned = contact.urns[7:-2]
                cls.objects.filter(uuid=contact.uuid).update(urns=cleaned)


class Message(models.Model):
    id = models.IntegerField(primary_key=True)
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
        return str(self.id)

    @classmethod
    def save_messages(cls, contact, msg_folder='Inbox'):
        client = TembaClient(settings.HOST, settings.KEY)
        messages = client.get_messages(folder=msg_folder).all()
        added = 0
        for message in messages:
            if not cls.message_exists(message):
                cls.objects.create(id=message.id, broadcast=message.broadcast, contact=contact,
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
        return cls.objects.filter(direction='out').all()

    @classmethod
    def sent_messages_count(cls):
        return cls.objects.filter(direction='out').count()

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

    @classmethod
    def add_email(cls, name, address):
        return cls.objects.create(name=name, address=address)

    @classmethod
    def send_message_email(cls, file_name):
        email_html_file = '<h4>Please see attached pdf report file</h4>'
        msg = EmailMessage('mCRAG weekly report', email_html_file, settings.EMAIL_HOST_USER, settings.MAILING_LIST)
        msg.attach_file(file_name)
        msg.content_subtype = "html"
        return msg.send()
