
from celery import task
import operator
import time

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

    intercom = conf.intercom_client
    intercom.events.create(event_name=name, user_id=user.id, metadata=properties, created_at=int(time.time()))


@task
def intercom_update_company(company_id, name, plan, custom_attributes):
    intercom = conf.intercom_client
    intercom.companies.create(company_id=company_id, name=name, plan=plan, custom_attributes=custom_attributes)

@task
def intercom_update_user(user_id, name, email, phone, signed_up_at, custom_attributes, companies):
    intercom = conf.intercom_client
    intercom.users.create(user_id=user_id, name=name, email=email, phone=phone, signed_up_at=signed_up_at, custom_attributes=custom_attributes, companies=companies)

