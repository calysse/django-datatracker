from django.conf import settings

MIXPANEL_TOKEN = "582f9de0d88d517e89c554f0ffb2e4f3"
MIXPANEL_FORWARD = getattr(settings, 'MIXPANEL_FORWARD', False)

try:
    from intercom import Intercom
    INTERCOM_FORWARD = getattr(settings, 'INTERCOM_FORWARD', False)
    Intercom.app_id = 'dnz2ak1z'
    Intercom.api_key = '49f8d434526edaf295ddc41a1c494569842841ff'
except AttributeError:
    INTERCOM_FORWARD = False

