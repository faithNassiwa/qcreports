from celery.decorators import task
from celery.utils.log import get_task_logger
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from .models import Group, Contact, Message


@periodic_task(run_every=(crontab(minute='*/3')), name="sync_groups", ignore_result=True)
def sync_groups():
    Group.add_groups()
    Group.get_group()
    Contact.clean_contacts()
    Message.clean_msg_contacts()


# @periodic_task(run_every=(crontab(minute='*/')), name="add_groups", ignore_result=True)
# def add_groups():
#     Group.add_groups()



