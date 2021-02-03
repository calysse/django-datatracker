from django_rq import job as task
import time
import logging
import datatracker.conf as conf
import traceback

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


def call_and_retry(function, *args, **kwargs):
    tries = 3
    for i in range(tries):
        try:
            function(*args, **kwargs)
        except Exception as e:
            if i < tries - 1:
                time.sleep(60)
                continue
            else:
                logger = logging.getLogger('graylog')
                logger.error(
                    "Intercom function '{}' failed with args: {} {}. Error message: {}.\n Traceback: {}".format(
                        function.__name__,
                        str(args),
                        str(kwargs),
                        str(e),
                        traceback.format_exc()))
                raise
        break


@task
def (firm_id):
    # [Seb] Avril 2020 Sync firm and Sub-firms data to Intercom
    from ipt.models import Firm
    from datetime import timedelta, datetime
    instance = Firm.objects.get(pk=int(firm_id))

    from datetime import date, timedelta
    instance.set_date_range(date.today() - timedelta(90), date.today())

    is_yooz = False
    is_yooz_expert = False
    is_yooz_business = False

    if instance.parent_firm and instance.parent_firm.id == 309:
        is_yooz = True
        if instance.edition == 'expert':
            is_yooz_expert = True
        if instance.edition == 'business':
            is_yooz_business = True

    custom_attributes = {'is_paid_account': instance.is_paid_account,
                         'nb_orgs': instance.nb_orgs,
                         'nb_active_orgs': instance.get_nb_active_orgs(),
                         'nb_collaborators': instance.profile_set.filter(user__is_staff=False).count(),
                         'nb_licences': instance.licenses,
                         'nb_used_licenses': instance.used_licenses,
                         'nb_free_licenses': instance.free_licenses,
                         'nb_available_licenses': instance.available_licenses,
                         'last_amount_due': instance.get_last_amount_due(),
                         'is_subfirm': instance.parent_firm is not None,
                         'is_yooz': is_yooz,
                         'is_yooz_expert': is_yooz_expert,
                         'is_yooz_business': is_yooz_business,
                         'new_org_within_30_days': instance.organisation_set.filter(created__gte=datetime.now()-timedelta(30)).count()
                         }

    custom_attributes['active_orgs_ratio'] = 0 if custom_attributes['nb_orgs'] == 0 else custom_attributes['nb_active_orgs'] * 100 // custom_attributes['nb_orgs']
    intercom = conf.intercom_client

    call_and_retry(intercom.companies.create,
                   company_id="F{}".format(str(firm_id)),
                   name="[FIRM] {}".format(instance.name),
                   custom_attributes=custom_attributes)


    owner_profile = instance.get_owner_profile()
    if owner_profile:
        owner = owner_profile.user

        intercom_update_user(owner.id,
                             "{} {}".format(owner.first_name, owner.last_name),
                             owner.email,
                             owner_profile.phone,
                             int(time.mktime(owner.date_joined.timetuple())),
                             {'is_firm_owner': True, 'is_accountant': True},
                             [{'company_id': "F{}".format(instance.id),
                               'name': "[FIRM] {}".format(instance.name)}])



@task
def intercom_update_company(company_id):
    from ipt.models import Organisation

    instance = Organisation.objects.get(pk=int(company_id))

    custom_attributes = {'is_gmail_connected': instance.is_gmail_connected,
                         'is_outlook_connected': instance.is_outlook_connected,
                         'is_email_bot_connected': instance.has_connect_email(),
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
                         'currency': instance.currency.name if instance.currency else "",
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
                         'last_mobile_use': int(time.mktime(instance.last_mobile_use.timetuple())),

                         # Stat data
                         'heard_from': str(instance.heard_from),
                         'nb_employees': str(instance.nb_employees),
                         'yearly_revenue': str(instance.yearly_revenue),
                         'company_legal_name': instance.company_legal_name,
                         'company_legal_type': instance.company_legal_type,
                         'headquarter_city': instance.headquarter_city,
                         'headquarter_zipcode': instance.headquarter_zipcode,
                         'headquarter_address': instance.headquarter_address,
                         'main_activity': instance.main_activity,

                         # Init treso flags
                         'treso_trial_started': False,
                         'treso_last_seen': 0,
                         'treso_30_days_sessions': 0,
                         'treso_categorization_completion': 0,
                         'treso_active_subscription': False,
                         'treso_has_churned': False,
                         'treso_plan': 'Trial',
                         'treso_trial_days': 0,
                         'treso_plan_monthly_value': 0,
                         'treso_nb_scenarios': 0
                         }

    # Treso app data - if loaded

    from treso.models import GlobalTresoSetting, Scenario, TresoWebSession
    global_treso_setting = GlobalTresoSetting.objects.filter(organisation=instance).last()
    last_seen = TresoWebSession.objects.last_seen(organisation=instance)

    if global_treso_setting and global_treso_setting.trial_period_start != None:
        custom_attributes.update({'treso_trial_started': True,
                                  'treso_first_seen': int(time.mktime(global_treso_setting.trial_period_start.timetuple())),
                                  'treso_last_seen': int(time.mktime(last_seen.timetuple())) if last_seen else 0,
                                  'treso_30_days_sessions': TresoWebSession.objects.get_thirty_days_websessions(instance),
                                  'treso_7_days_sessions': TresoWebSession.objects.get_seven_days_websessions(instance),
                                  'treso_categorization_completion': global_treso_setting.get_categorization_completion(),
                                  'treso_active_subscription': global_treso_setting.treso_active_plan is not None,
                                  'treso_trial_days': global_treso_setting.trial_days(),
                                  'treso_has_churned': global_treso_setting.treso_has_churned,
                                  'treso_plan': global_treso_setting.treso_active_plan.name if global_treso_setting.treso_active_plan else 'Trial',
                                  'treso_plan_monthly_value': global_treso_setting.treso_active_plan.get_yearly_monthly_value() if global_treso_setting.treso_active_plan else 0,
                                  'treso_nb_scenarios': Scenario.objects.filter(organisation=instance).count()
                                  })

    intercom = conf.intercom_client
    call_and_retry(intercom.companies.create,
                   company_id=str(company_id),
                   name=instance.name,
                   plan=instance.get_plan(),
                   custom_attributes=custom_attributes,
                   monthly_spend=instance.monthly_spend)


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
    from intercom.errors import ResourceNotFound
    intercom = conf.intercom_client
    try:
        intercom_user = intercom.users.find(user_id=user_id)
        intercom_lead = intercom.leads.find(id=lead_id)
    except ResourceNotFound:
        intercom_user = None
        intercom_lead = None
    if intercom_user and intercom_lead:
        return intercom.leads.convert(intercom_lead, intercom_user)
    else:
        return None
