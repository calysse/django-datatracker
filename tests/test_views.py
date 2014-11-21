__author__ = 'sebastienclaeys'

from data_tracker import views
import common.tests as test_helper

class Ab_exp_statusTestCase(test_helper.ViewTestCase):
    def pre_test(self):
        self.view = views.ab_exp_status
        self.view_args = (1,)

class User_targetTestCase(test_helper.ViewTestCase):
    def pre_test(self):
        self.view = views.user_target
        self.view_args = (10000,)

class User_aquiredTestCase(test_helper.ViewTestCase):
    def pre_test(self):
        self.view = views.user_acquired
        self.view_args = ()
