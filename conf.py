from django.conf import settings

DT_MIXPANEL_FORWARD = getattr(settings, 'DT_MIXPANEL_FORWARD', False)
DT_INTERCOM_FORWARD = getattr(settings, 'DT_INTERCOM_FORWARD', False)
DT_LOCAL_SAVE = getattr(settings, 'DT_LOCAL_SAVE', True)

DT_MIXPANEL_TOKEN = getattr(settings, 'DT_MIXPANEL_TOKEN', False)

if DT_INTERCOM_FORWARD:
    DT_INTERCOM_APPID = getattr(settings, 'DT_INTERCOM_APPID')
    DT_INTERCOM_TOKEN = getattr(settings, 'DT_INTERCOM_TOKEN')

    from intercom.client import Client
    intercom_client = Client(personal_access_token=DT_INTERCOM_TOKEN)
    # Intercom.app_id = DT_INTERCOM_APPID
    # Intercom.api_key = DT_INTERCOM_TOKEN  # Deprecated intercom client

