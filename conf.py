from django.conf import settings

DT_MIXPANEL_FORWARD = getattr(settings, 'DT_MIXPANEL_FORWARD', False)
DT_INTERCOM_FORWARD = getattr(settings, 'DT_INTERCOM_FORWARD', False)
DT_LOCAL_SAVE = getattr(settings, 'DT_LOCAL_SAVE', False)

DT_MIXPANEL_TOKEN = "7d737864ce0c6cb65d071e8b09c74fc6"
DT_INTERCOM_APP_ID = "eiildktn"
DT_INTERCOM_API_KEY = "0186775356d7f3b7e27cac57009ada5326f49c84"

if DT_INTERCOM_FORWARD:
    from intercom import Intercom
    Intercom.app_id = DT_INTERCOM_APP_ID
    Intercom.api_key = DT_INTERCOM_API_KEY

