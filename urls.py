__author__ = 'sebastienclaeys'

from django.conf.urls import url

import datatracker.views

urlpatterns = [
    url(r'^stats/(\w+)$', datatracker.views.stats),
    url(r'^weekly/$', datatracker.views.compare_weeks),
    url(r'^gevents/$', datatracker.views.events_gen),
    url(r'^cohort/$', datatracker.views.cohort),
    url(r'^forecast/$', datatracker.views.prevision),
]
