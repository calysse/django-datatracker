__author__ = 'sebastienclaeys'

import datatracker.models as model
import datatracker.conf as conf
import datatracker.tasks as task_queue


def track(user, name, properties={}, group=None):
    model.Event.objects.create(user=user if isinstance(user, model.User) else None, name=name, group=group, properties=properties)
    if conf.MIXPANEL_FORWARD:
        task_queue.mp_track.delay(user, name, properties)

def intercom_track(user, name, properties):
    if conf.INTERCOM_FORWARD:
        task_queue.intercom_track.delay(user, name, properties)

def intercom_tags(user, name, tag_or_untag):
    if conf.INTERCOM_FORWARD:
        task_queue.intercom_tags.delay(user, name, tag_or_untag)


# Mixpannel wrapper for compatibility purpose
def people_set(user, properties={}):
    if conf.MIXPANEL_FORWARD:
        task_queue.mp_people_set.delay(user, properties)
