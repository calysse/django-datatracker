__author__ = 'sebastienclaeys'

from django.db import models
from django.contrib.auth.models import User
from const import APP_NAME
import common.fields.dictionary as dictionary_field
from data_tracker.models import const

from django.conf import settings as conf
from datetime import datetime

class EventManager(models.Manager):
    def retrieve(self, GET, names):
        from datetime import timedelta
        start = datetime.strptime(GET['start'], '%Y%m%d')
        end = datetime.strptime(GET['end'], '%Y%m%d')
        qs = self.filter(datetime__range=[start, end + timedelta(1)], name__in=names)

        return qs.order_by('datetime')


class Event(models.Model):
    # def __init__(self, *args, **kwargs):
    #     super(Event, self).__init__(*args, **kwargs)
    #     self.__dict__.update(self.properties)

    name = models.CharField(max_length=64, db_index=True)
    group = models.CharField(max_length=64, db_index=True, blank=True)
    user = models.ForeignKey(User, blank=True, null=True, default=None, db_index=True)
    properties = dictionary_field.DictionaryField(default=None, null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    date = models.DateField(auto_now_add=True, db_index=True)

    objects = EventManager()

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = APP_NAME

