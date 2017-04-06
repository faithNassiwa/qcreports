from django.db import models
from django.conf import settings
from temba_client.v2 import TembaClient


# Create your models here.
class Contact(models.Model):
    uuid = models.CharField(max_length=200)
    name = models.CharField(max_length=200, null=True)
    language = models.CharField(max_length=200, null=True)
    urns = models.CharField(max_length=200)
    groups = models.CharField(max_length=250)
    fields = models.CharField(max_length=200)
    blocked = models.BooleanField(default=False)
    stopped = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(null=True)

    def __str__(self):
        return self.uuid

    @classmethod
    def save_contacts(cls):
        client = TembaClient(settings.HOST, settings.KEY)
        contacts = client.get_contacts().all()
        added = 0
        for contact in contacts:
            if not cls.contact_exists(contact):
                cls.objects.create(uuid=contact.uuid, name=contact.name, language=contact.language,
                                   urns=contact.urns, groups=contact.groups, fields=contact.fields,
                                   blocked=contact.blocked, stopped=contact.stopped,
                                   created_on=contact.created_on, modified_on=contact.modified_on)
                added += 1
        return added

    @classmethod
    def contact_exists(cls, contact):
        return cls.objects.filter(uuid=contact.uuid).exists()


class Message(models.Model):
    id = models.IntegerField(primary_key=True)
    broadcast = models.IntegerField(null=True)
    contact = models.CharField(max_length=200)
    urn = models.CharField(max_length=200)
    channel = models.CharField(max_length=200)
    direction = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    status = models.CharField(max_length=200)
    visibility = models.CharField(max_length=200)
    text = models.CharField(max_length=1000)
    labels = models.CharField(max_length=200)
    created_on = models.DateTimeField(auto_now_add=True)
    sent_on = models.DateTimeField(null=True)
    modified_on = models.DateTimeField(null=True)

    def __str__(self):
        return self.id

    @classmethod
    def save_messages(cls):
        client = TembaClient(settings.HOST, settings.KEY)
        messages = client.get_messages(folder='Inbox').all()
        added = 0
        for message in messages:
            if not cls.message_exists(message):
                cls.objects.create(id=message.id, broadcast=message.broadcast, contact=message.contact,
                                   urn=message.urn, channel=message.channel, direction=message.direction,
                                   type=message.type, status=message.status, visibility=message.visibility,
                                   text=message.text, labels=message.labels, created_on=message.created_on,
                                   sent_on=message.sent_on, modified_on=message.modified_on)
                added += 1
        return added

    @classmethod
    def message_exists(cls, message):
        return cls.objects.filter(id=message.id).exists()
