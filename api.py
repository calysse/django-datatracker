__author__ = 'sebastienclaeys'

import datatracker.models as model
import datatracker.conf as conf
import datatracker.tasks as task_queue

def track(user, name, properties, group=None):
    if conf.DT_LOCAL_SAVE:
        model.Event.objects.create(user=user if isinstance(user, model.User) else None, name=name, group=group, properties=properties)
    if conf.DT_MIXPANEL_FORWARD:
        task_queue.mp_track.delay(user, name, properties)
    if conf.DT_INTERCOM_FORWARD:
        task_queue.intercom_track.delay(user, name, properties)

def people_set(user, properties):
    if conf.DT_MIXPANEL_FORWARD:
        task_queue.mp_people_set.delay(user, properties)
