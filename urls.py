__author__ = 'sebastienclaeys'

from django.conf.urls import url, patterns

urlpatterns = patterns('datatracker.views',
    (r'^stats/(\w+)$', 'stats'),
    (r'^weekly/$', 'compare_weeks'),
    (r'^gevents/$', 'events_gen'),
    (r'^cohort/$', 'cohort'),
    (r'^forecast/$', 'prevision'),
)
