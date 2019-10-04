from __future__ import print_function, generators, division, unicode_literals, absolute_import

__author__ = 'sebastienclaeys'

from django.conf.urls import url

import datatracker.views

urlpatterns = [
    url(r'^stats/(\w+)$', datatracker.views.stats, name='datatracker.views.stats'),
    url(r'^weekly/$', datatracker.views.compare_weeks, name='datatracker.views.compare_weeks'),
    url(r'^gevents/$', datatracker.views.events_gen, name='datatracker.views.events_gen'),
    url(r'^cohort/$', datatracker.views.cohort, name='datatracker.views.cohort'),
    url(r'^forecast/$', datatracker.views.prevision, name='datatracker.views.prevision'),
]
