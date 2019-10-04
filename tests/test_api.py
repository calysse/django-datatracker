from __future__ import print_function, generators, division, unicode_literals, absolute_import

__author__ = 'sebastienclaeys'

from ipt.tests.base import BaseTestCase
from django.urls import reverse
import datatracker.models as model

class TrackTestCase(BaseTestCase):

    def test_views(self):
        res = self.client.get(reverse('datatracker.views.events_gen') + "?metric=group,name,filter:value,agg")
        self.assertEqual(res.status_code, 200)

        # res = self.client.get(reverse('datatracker.views.compare_weeks'))
        # self.assertEqual(res.status_code, 200)
        #
        # res = self.client.get(reverse('datatracker.views.cohort'))
        # self.assertEqual(res.status_code, 200)
        #
        # res = self.client.get(reverse('datatracker.views.prevision'))
        # self.assertEqual(res.status_code, 200)


    def test_details(self):
        import datatracker.api as api
        import time

        event_name = "Test event #%d" % int(time.time())
        group_name = "Test group"
        properties = {'test_property': 'test_value'}

        # Deleting all existing events for the test group
        qs = model.Event.objects.filter(group=group_name)
        qs.delete()

        # Track an event
        api.track(self.test_user, event_name, properties, group=group_name)

        qs = model.Event.objects.filter(group=group_name)
        self.assertEqual(len(qs), 1, "Query set should have one item")

        event = qs[0]
        self.assertEqual(event.name, event_name, "Event name mismatch")
        self.assertEqual(event.properties, properties, "Properties content mismatch")
