
from celery import task
import operator

import datatracker.conf as conf


@task
def mp_people_set(user, properties):
    import mixpanel
    mp = mixpanel.Mixpanel(conf.DT_MIXPANEL_TOKEN)

    data = {
        '$first_name'    : user.first_name,
        '$last_name'     : user.last_name,
        '$email'         : user.email,
        '$phone'         : user.profile.phone,
    }

    data.update(properties)
    mp.people_set(user.email, data)


@task
def mp_track(user, name, properties):
    import mixpanel
    mp = mixpanel.Mixpanel(conf.DT_MIXPANEL_TOKEN)
    mp.track(user.email if user else 0, name, properties)


@task
def intercom_track(user, name, properties = None):
    if properties is None:
        properties = {}

    from intercom import Event
    # User.create(user_id=user.id)
    Event.create(event_name=name, email=user.email, metadata=properties)

