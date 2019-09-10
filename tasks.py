
from django_rq import job as task
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
    try:
        intercom.events.create(event_name=name, user_id=user.id, metadata=properties, created_at=int(time.time()))
    except:
        pass


@task
def intercom_update_company(company_id, name, plan, custom_attributes, monthly_spend=0):
    intercom = conf.intercom_client
    intercom.companies.create(company_id=company_id, name=name, plan=plan, custom_attributes=custom_attributes, monthly_spend=monthly_spend)


@task
def intercom_update_user(user_id, name, email, phone, signed_up_at, custom_attributes, companies):
    intercom = conf.intercom_client
    if companies is None:
        intercom.users.create(user_id=user_id, name=name, email=email, phone=phone, signed_up_at=signed_up_at,
                              custom_attributes=custom_attributes)
    else:
        intercom.users.create(user_id=user_id, name=name, email=email, phone=phone, signed_up_at=signed_up_at,
                              custom_attributes=custom_attributes, companies=companies)


@task
def intercom_update_user_custom_attributes(user_id, custom_attributes):
    intercom = conf.intercom_client
    intercom.users.create(user_id=user_id, custom_attributes=custom_attributes)



@task
def intercom_update_lead(name, email, custom_attributes):
    intercom = conf.intercom_client
    return intercom.leads.create(name=name, email=email, custom_attributes=custom_attributes)


@task
def intercom_convert_lead(lead_id, user_id):
    intercom = conf.intercom_client
    intercom_user = intercom.users.find(user_id=user_id)
    intercom_lead = intercom.leads.find(id=lead_id)
    return intercom.leads.convert(intercom_lead, intercom_user)
