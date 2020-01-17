
from django_rq import job as task
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
def intercom_update_company(company_id):
    from ipt.models import Organisation

    instance = Organisation.objects.get(pk=int(company_id))

    custom_attributes = {'is_gmail_connected': instance.is_gmail_connected,
                         'is_outlook_connected': instance.is_outlook_connected,
                         'is_email_bot_connected': instance.is_outlook_connected or instance.is_gmail_connected or instance.is_imap_connected,
                         'is_slack_connected': instance.is_slack_connected,
                         'is_gmail_active': instance.is_gmail_active,
                         'accountant_invited': instance.accountant_invited,
                         'country': instance.country,
                         'has_card': instance.has_card,
                         'is_real_churn': instance.is_real_churn,
                         'is_trial_churn': instance.is_trial_churn,
                         'is_referral': instance.is_referral(),
                         'invoice_created': instance.invoice_created,
                         'phone': instance.phone,
                         'utm_medium': instance.utm_medium,
                         'utm_source': instance.utm_source,
                         'utm_campaign': instance.utm_campaign,
                         'utm_content': instance.utm_content,
                         'http_referrer': instance.http_referrer,
                         'ref_leads': instance.ref_leads,
                         'refered_orgs': instance.referred_orgs.all().count(),
                         'affiliate': instance.get_afp_org(),
                         'currency': instance.currency.name,
                         'nb_members': instance.members.all().count(),
                         'nb_collectors': instance.collectorinstance_set.count(),
                         'nb_invoices': instance.inv_invoice.count(),
                         'nb_expense_users': instance.expenseuser_set.count(),
                         'firm': u"#{} {}".format(instance.firm.id,
                                                  instance.firm.name) if instance.firm else "",
                         'nb_siblings': instance.firm.organisation_set.count() if instance.firm else 0,
                         'website': instance.website,
                         'is_bankin_connected': instance.is_bankin_connected(),
                         'signup_step': instance.signup_step,
                         'last_dashboard': int(time.mktime(instance.last_dashboard.timetuple())),
                         'mobile_scanner_link_sent': instance.mobile_scanner_link_sent,
                         'last_mobile_use': int(time.mktime(instance.last_mobile_use.timetuple()))
                         }

    intercom = conf.intercom_client

    intercom.companies.create(company_id=str(company_id), name=instance.name, plan=instance.get_plan(), custom_attributes=custom_attributes, monthly_spend=instance.monthly_spend)


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
