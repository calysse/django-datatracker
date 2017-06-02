__author__ = 'sebastienclaeys'

from django.db import models
from django.contrib.auth.models import User
from const import APP_NAME
import common.fields.dictionary as dictionary_field

from datetime import datetime

class EventManager(models.Manager):
    def retrieve(self, GET, names):
        from datetime import timedelta
        start = datetime.strptime(GET['start'], '%Y%m%d')
        end = datetime.strptime(GET['end'], '%Y%m%d')
        qs = self.filter(datetime__range=[start, end + timedelta(1)], name__in=names)

        return qs.order_by('datetime')


    def new_inst(self, name, user=None, company=None, group=None, properties=None, datetime=None):
        if company and type(company) != int:
            company = company.id

        if user and type(user) != int:
            user = user.id

        if datetime is not None:
            event = Event(user=user, company=company, name=name, group=group, properties=properties, datetime=datetime)
        else:
            event = Event(user=user, company=company, name=name, group=group, properties=properties)

        return event


    def add(self, *args, **kwargs):
        event = self.new_inst(*args, **kwargs)
        event.save()
        return event


    def batch_add(self, events):
        batch = []
        for event in events:
            batch.append(self.new_inst(**event))

        self.bulk_create(batch)


    def clear(self, group=None, name=None, user=None, company=None):
        qs = self.all()

        if group is None and name is None and user is None and company is None:
            print "Need at least one filter."  # Protection to prevent all event deletion
            return 0

        if group:
            qs = qs.filter(group=group)

        if user:
            qs = qs.filter(user=user)

        if name:
            qs = qs.filter(name=name)

        if company:
            qs = qs.filter(company=company)

        count = qs.count()
        qs.delete()

        return count



class Event(models.Model):
    name = models.CharField(max_length=64)
    group = models.CharField(max_length=64, blank=True)
    user = models.IntegerField(blank=True, null=True, default=None)
    company = models.IntegerField(blank=True, null=True, default=None)
    properties = dictionary_field.DictionaryField(default=None, null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True)

    objects = EventManager()

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = APP_NAME

