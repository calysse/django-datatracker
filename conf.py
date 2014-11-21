from django.conf import settings as conf


try:
    MIXPANEL_FORWARD = conf.MIXPANEL_MIXPANEL_FORWARD
    MIXPANEL_TOKEN = "582f9de0d88d517e89c554f0ffb2e4f3"
except AttributeError:
    MIXPANEL_FORWARD = False

try:
    INTERCOM_FORWARD = conf.INTERCOM_FORWARD
    from intercom import Intercom
    Intercom.app_id = 'dnz2ak1z'
    Intercom.api_key = '49f8d434526edaf295ddc41a1c494569842841ff'
except AttributeError:
    INTERCOM_FORWARD = False
