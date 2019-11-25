
__author__ = 'sebastienclaeys'

from ipt.tests.base import BaseTestCase
from django.urls import reverse
import datatracker.models as model
from datetime import datetime, timedelta
import random



class DatatrackerViewsTestCase(BaseTestCase):

    def _generate_org_signup_events(self):
        event_name = "org_signup"
        group_name = "gen_orgs"
        properties = {'plan': 'essential',
                      'utm_source': None,
                      'utm_medium': None,
                      'utm_campaign': None,
                      'utm_content': None,
                      'activation': 0,
                      'is_churn': False,
                      'is_paid': True,
                      'is_direct': True,
                      'is_license': False,
                      'is_monthly': True,
                      'is_yearly': False,
                      'is_referral': False,
                      'is_pro': False,
                      'is_standard': True
                      }

        import datatracker.api as api

        from_date = datetime(2019,1,1)
        to_date = datetime(2019,11,19)
        delta = (to_date - from_date).days

        print("Generating events..")
        for i in range(2000):
            api.track(None, event_name, properties, group=group_name, datetime=from_date + timedelta(random.randrange(delta)), test_mode=True)


    def test_gen_events(self):
        # Calling following view
        # gen_orgs,org_signup,is_paid:True,,&agg_by=utm_source&start=20190101&end=20191119
        self._generate_org_signup_events()

        res = self.client.get(reverse('datatracker.views.events_gen') + "?metric=gen_orgs,org_signup,is_paid:True,,&agg_by=utm_source&start=20190101&end=20191119")