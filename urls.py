__author__ = 'sebastienclaeys'

from django.conf.urls import url, patterns

urlpatterns = patterns('data_tracker.views',
    (r'^user_target/(\d+)$', 'user_target'),
    (r'^ab_exp_status/(\d+)$', 'ab_exp_status'),
    (r'^user_acquired$', 'user_acquired'),
    (r'^user_segmentation/(\w+)$', 'user_segmentation'),
    (r'^stats/(\w+)$', 'stats'),
    (r'^data/(\w+)/(\w+)/(\w+)$', 'esdata'),
    (r'^events/$', 'events'),
    (r'^weekly/$', 'compare_weeks'),
    (r'^gevents/$', 'events_gen'),
    (r'^forecast/$', 'prevision'),
)
