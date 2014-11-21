__author__ = 'sebastienclaeys'

import common.tests as test_helper
import data_tracker.models as model

class TrackTestCase(test_helper.LoggedInTestCase):
    def test_details(self):
        import data_tracker.api as api
        import time

        event_name = "Test event #%d" % int(time.time())
        group_name = "Test group"
        properties = {'test_property': 'test_value'}


        # Deleting all existing events for the test group
        qs = model.Event.objects.filter(group=group_name)
        qs.delete()

        # Track an event
        api.track(self.user, event_name, properties, group=group_name)

        qs = model.Event.objects.filter(group=group_name)
        self.assertEqual(len(qs), 1, "Query set should have one item")

        event = qs[0]
        self.assertEqual(event.name, event_name, "Event name mismatch")
        self.assertEqual(event.properties, properties, "Properties content mismatch")

