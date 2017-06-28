__author__ = 'sebastienclaeys'

import datatracker.models as model
import datatracker.conf as conf
import datatracker.tasks as task_queue

def track(user, name, properties, group=None, company=None, datetime=None):
    if conf.DT_LOCAL_SAVE:
        model.Event.objects.add(user=user if isinstance(user, model.User) else None, name=name, group=group, properties=properties, datetime=datetime, company=company)
    if conf.DT_MIXPANEL_FORWARD:
        task_queue.mp_track.delay(user, name, properties)
    if conf.DT_INTERCOM_FORWARD:
        if conf.DEBUG:
            # task_queue.intercom_track(user, name, properties)
            pass
        else:
            task_queue.intercom_track.delay(user, name, properties)


def batch_track(events):
    if conf.DT_LOCAL_SAVE:
        model.Event.objects.batch_add(events)

def clear(user=None, company=None, name=None, group=None):
    model.Event.objects.clear(user=user, name=name, group=group, company=company)

def people_set(user, properties):
    if conf.DT_MIXPANEL_FORWARD:
        task_queue.mp_people_set.delay(user, properties)

def get_intercom_client():
    return conf.intercom_client