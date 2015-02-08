from django.conf import settings

MIXPANEL_TOKEN = "582f9de0d88d517e89c554f0ffb2e4f3"
MIXPANEL_FORWARD = getattr(settings, 'MIXPANEL_FORWARD', False)
INTERCOM_FORWARD = False

