from django.test import TestCase
from .models import Contact, Message, Group, Run, Value, Step, Flow
from django.utils import timezone


class DumpTest(TestCase):
    def test_one_plus_one(self):
        self.assertEquals(1 + 1, 2)


class TestGroup(TestCase):
    def test_add_groups(self):
        group_count = Group.objects.count()
        added_groups = Group.add_groups()
        self.assertEquals(Group.objects.count(), group_count + added_groups)

    def test_group_exists(self):
        class G(object):
            def __init__(self, name=None, uuid=None, query=None, count=None):
                self.name = name
                self.uuid = uuid
                self.query = query
                self.count = count

        qc_mock_group = G(name='Test Group', uuid='random number', query=None, count=4)
        self.assertEquals(Group.group_exists(qc_mock_group), False)
        Group.objects.create(name='Test Group', uuid='random number', query=None, count=4)
        self.assertEquals(Group.group_exists(qc_mock_group), True)


class TestContact(TestCase):
    def setUp(self):
        Group.objects.create(uuid="23fg", name="test-group", query="test", count=2)

    def test_add_contacts(self):
        contact_count = Contact.objects.count()
        group = Group.objects.first()
        added_contacts = Contact.save_contacts(group=group)
        self.assertEquals(Contact.objects.count(), contact_count + added_contacts)

    def test_contact_exists(self):
        class C(object):
            def __init__(self, id=None, uuid=None, name=None, language=None, urns=None,
                         groups=None, fields=None, blocked=None, stopped=None, created_on=None, modified_on=None):
                self.id = id
                self.uuid = uuid
                self.name = name
                self.language = language
                self.urns = urns
                self.groups = groups
                self.fields = fields
                self.blocked = blocked
                self.stopped = stopped
                self.created_on = created_on
                self.modified_on = modified_on

        group = Group.objects.first()
        qc_mock_contact = C(uuid="uuid-test", name="name-test", language="language-test", urns="urns-test",
                            groups=group, fields="fields-test", blocked=False, stopped=False, created_on=None,
                            modified_on=None)
        self.assertEquals(Contact.contact_exists(qc_mock_contact), False)
        Contact.objects.create(uuid="uuid-test", name="name-test", language="language-test", urns="urns-test",
                               groups=group, fields="fields-test", blocked=False, stopped=False,
                               created_on=None, modified_on=None)
        self.assertEquals(Contact.contact_exists(qc_mock_contact), True)


class TestMessage(TestCase):
    def setUp(self):
        group = Group.objects.create(uuid="23fg", name="test-group", query="test", count=2)
        Contact.objects.create(uuid="uuid-test", name="name-test", language="language-test", urns="urns-test",
                               groups=group, fields="fields-test", blocked=False, stopped=False,
                               created_on=None, modified_on=None)

    def test_add_messages(self):
        contact = Contact.objects.first()
        message_count = Message.objects.count()
        added_messages = Message.save_messages(contact, msg_folder=['sent'])
        self.assertEquals(Message.objects.count(), message_count + added_messages)

    def test_message_exists(self):
        class M(object):
            def __init__(self, id=None, folder=None, broadcast=None, contact=None, urn=None, channel=None,
                         direction=None, type=None, status=None, visibility=None, text=None, labels=None,
                         created_on=None, sent_on=None, modified_on=None):
                self.id = id
                self.folder = folder
                self.broadcast = broadcast
                self.contact = contact
                self.urn = urn
                self.channel = channel
                self.direction = direction
                self.type = type
                self.status = status
                self.visibility = visibility
                self.text = text
                self.labels = labels
                self.sent_on = sent_on
                self.created_on = created_on
                self.modified_on = modified_on

        contact = Contact.objects.first()
        qc_mock_message = M(id=1, broadcast=1, contact=contact, urn="urn-test", channel="channel-test",
                            direction="direction-test", type="type-test", status="status-test",
                            visibility="visibility-test", text="text-test", labels="labels-test", created_on=None,
                            sent_on=None, modified_on=None)
        self.assertEquals(Message.message_exists(qc_mock_message), False)
        Message.objects.create(id=1, broadcast=1, contact=contact, urn="urn-test", channel="channel-test",
                               direction="direction-test", type="type-test", status="status-test",
                               visibility="visibility-test", text="text-test", labels="labels-test", created_on=None,
                               sent_on=None, modified_on=None)
        self.assertEquals(Message.message_exists(qc_mock_message), True)


class TestRun(TestCase):
    def setUp(self):
        group = Group.objects.create(uuid="23fg", name="test-group", query="test", count=2)
        Contact.objects.create(uuid="uuid-test", name="name-test", language="language-test", urns="urns-test",
                               groups=group, fields="fields-test", blocked=False, stopped=False,
                               created_on=None, modified_on=None)

    def test_add_runs(self):
        contact = Contact.objects.first()
        run_count = Run.objects.count()
        added_runs = Run.add_runs(contact)
        self.assertEquals(Run.objects.count(), run_count + added_runs)

    def test_run_exists(self):
        class T(object):
            def __init__(self, id=None, run_id=None, responded=None, created_on=None, modified_on=None, exit_type=None,
                         contact=None):
                self.id = run_id
                self.run_id = run_id
                self.responded = responded
                self.created_on = created_on
                self.modified_on = modified_on
                self.exit_type = exit_type
                self.contact = contact

        contact_object = Contact.objects.first()
        rapidpro_mock_run = T(id=6, run_id=6, responded=False, created_on=timezone.now(), modified_on=timezone.now(),
                              exit_type='completed', contact=contact_object)
        self.assertEquals(Run.run_exists(rapidpro_mock_run), False)
        Run.objects.create(id=6, run_id=6, responded=False, created_on=timezone.now(), modified_on=timezone.now(),
                           exit_type='completed', contact=contact_object)
        self.assertEquals(Run.run_exists(rapidpro_mock_run), True)


class TestFlow(TestCase):
    def setUp(self):
        group = Group.objects.create(uuid="23fg", name="test-group", query="test", count=2)
        Contact.objects.create(uuid="uuid-test", name="name-test", language="language-test",
                               urns="urns-test", groups=group, fields="fields-test", blocked=False,
                               stopped=False, created_on=None, modified_on=None)
        c = Contact.objects.first()
        run = Run.objects.create(id=6, run_id=6, responded=False, created_on=timezone.now(), modified_on=timezone.now(),
                                 exit_type='completed', contact=c)
        Flow.objects.create(uuid='788ghh', name='flow-test', run_id=run)

    def test_add_steps(self):
        run_object = Run.objects.first()
        flow = Flow.objects.first()
        flow_count = Flow.objects.count()
        added_flow = Flow.add_flows(run_object, flow)
        self.assertEquals(Flow.objects.count(), flow_count + added_flow)


class TestStep(TestCase):
    def setUp(self):
        group = Group.objects.create(uuid="23fg", name="test-group", query="test", count=2)
        Contact.objects.create(uuid="uuid-test", name="name-test", language="language-test",
                               urns="urns-test", groups=group, fields="fields-test", blocked=False,
                               stopped=False, created_on=None, modified_on=None)
        c = Contact.objects.first()
        run = Run.objects.create(id=6, run_id=6, responded=False, created_on=timezone.now(), modified_on=timezone.now(),
                                 exit_type='completed', contact=c)
        Step.objects.create(node='788ghh', time=timezone.now(), run_id=run)

    def test_add_steps(self):
        run_object = Run.objects.first()
        steps = Step.objects.all()
        step_count = Step.objects.count()
        added_steps = Step.add_steps(run_object, steps)
        self.assertEquals(Step.objects.count(), step_count + added_steps)


class TestValue(TestCase):
    def setUp(self):
        group = Group.objects.create(uuid="23fg", name="test-group", query="test", count=2)
        Contact.objects.create(uuid="uuid-test", name="name-test", language="language-test",
                               urns="urns-test", groups=group, fields="fields-test", blocked=False,
                               stopped=False, created_on=None, modified_on=None)
        c = Contact.objects.first()
        run = Run.objects.create(id=6, run_id=6, responded=False, created_on=timezone.now(), modified_on=timezone.now(),
                                 exit_type='completed', contact=c)
        Value.objects.create(value='testing', run_id=run)

    def test_add_values(self):
        run_object = Run.objects.first()
        values = Value.objects.all()
        value_count = Value.objects.count()
        added_values = Value.add_values(run_object, values)
        self.assertEquals(Value.objects.count(), value_count + added_values)
