__author__ = 'sebastienclaeys'

#####################
# User Segmentation
#####################
import datatracker.models as dt_model
from datetime import datetime, timedelta, date


DATA_FUNC = {}

def register_data_func(func):
    global DATA_FUNC
    DATA_FUNC[func.__name__] = func


def get_events_queryset(metric):
    mtuple = metric.split(',')
    group, name, filter_by = mtuple

    events = dt_model.Event.objects.all().order_by('-datetime')

    if len(filter_by):
        filter_by = {x[0]: x[1] for x in map(lambda y: y.split(':'), filter_by.split(';'))}

    if len(group) and group != '*':
        events = events.filter(group=group)

    if len(name) and name != '*':
        events = events.filter(name=name)

    return events, filter_by


def get_cohort_metric_matrix(metric, granularity, nb_items):

    def _get_key(event):
        if granularity == 'day':
            key = event.datetime.strftime("%Y%m%d")
        elif granularity == 'week':
            key = (event.datetime - timedelta(event.datetime.weekday())).strftime("%Y%m%d")
        else:
            key = event.datetime.strftime("%Y%m")
        return key

    metric_matrix = {}
    events, filter_by = get_events_queryset(metric)
    chunk_number = 0
    for event in events:
        if filter_by:
            passe = True
            for key, val in filter_by.items():
                if not key in event.properties:
                    passe = False
                elif val != '*' and str(event.properties[key]) != val:
                    passe = False
            if not passe:
                continue

        key = _get_key(event)

        if not key in metric_matrix:
            if chunk_number >= nb_items:
                break

            metric_matrix[key] = [chunk_number, set()]
            chunk_number += 1
        else:
            metric_matrix[key][1].add(event.user)

    return metric_matrix


def cohorts(main_metric, trigger_metric, granularity='week', nb_items=12):
    # 1 segment events users by key (for both events)
    # for each granularity level, output the len of the main set, and then for each subkey, output the intersection of the main set and the subset

    main_metric_matrix = get_cohort_metric_matrix(main_metric, granularity, nb_items)
    trigger_metric_matrix = get_cohort_metric_matrix(trigger_metric, granularity, nb_items)

    cohort = []

    for mkey in sorted(main_metric_matrix.keys()):
        user_set = main_metric_matrix[mkey][1]
        res = [mkey, len(user_set)]
        offset = 0
        for tkey in sorted(trigger_metric_matrix.keys()):
            if tkey < mkey:
                continue
            trigger_user_set = trigger_metric_matrix[tkey][1]
            intersect = user_set.intersection(trigger_user_set)
            res.append(len(intersect))
        cohort.append(res)

    return cohort


# Generic get events
#
# name=name of the event, e.g. 'Member acquired'
# group=group of event, e.g. 'Member activity'
# start, end = YYYYMMDD = date range in which we aggregate the events
# filter_by_properties = {}. e.g. {'City': 'Paris'} will take only events where 'City' = 'Paris' is in the property dict
# aggregate_by_properties = 'property_name'. e.g. 'City', will aggregate the result by 'City' instead of by date (default)
# count_by_property = 'property name', e.g. 'Nb sent', will aggregate the value of the property Nb send instead if just counting the nuber of event (default)
#
def get_events(name, group, start=None, end=None, filter_by_properties=None, aggregate_by=None, count_by_property=None, override_name=None):
    EventModel = dt_model.Event

    if start is not None and end is not None:
        dstart = datetime.strptime(start, '%Y%m%d') if type(start) in [str, unicode] else start
        dend = (datetime.strptime(end, '%Y%m%d') if type(end) in [str, unicode] else end) + timedelta(1)
        #events = dt_model.Event.objects.filter(datetime__range=[dstart, dend]).order_by('-datetime')
        events = EventModel.objects.filter(datetime__gt=dstart, datetime__lt=dend).order_by('-datetime')
    else:
        events = EventModel.objects.all().order_by('-datetime')

    if len(group) and group != '*':
         events = events.filter(group=group)

    if len(name) and name != '*':
         events = events.filter(name=name)


    res = {}
    for event in events:
        # Filtering by properties
        cat_key = name if not override_name else override_name

        if group == '*':
            cat_key = cat_key + ' %s' % event.group

        if name == '*':
            cat_key = cat_key + ' %s' % event.name

        if filter_by_properties:
            passe = True
            for key, val in filter_by_properties.items():
                if not key in event.properties:
                    passe = False
                elif val != '*' and str(event.properties[key]) != val:
                    passe = False
                elif val == '*':
                    cat_key = cat_key + ' %s' % event.properties[key]
            if not passe:
                continue

        if not cat_key in res:
            res[cat_key] = {}

        if aggregate_by == None or aggregate_by == 'date': # Default, aggregate by date
            key = event.datetime.date().strftime("%Y%m%d")
        elif aggregate_by == 'group': # Aggregate by group name
            key = event.group
        elif aggregate_by == 'name': # Aggregate by event name
            key = event.name
        else: # Aggregate by property value
            key = event.properties[aggregate_by]


        if not key in res[cat_key]:
            res[cat_key][key] = 0

        if not count_by_property:
            # Counting event count
            res[cat_key][key] += 1
        elif count_by_property in event.properties:
            # Counting by properties
            res[cat_key][key] += event.properties[count_by_property]

    return res
    #return sorted(res.items(), key=operator.itemgetter(int(sortby)), reverse=(sortby[0] == '-'))



def scan_metric(group, name, filter_by, count, offset):
    today = date.today()
    monday = today - timedelta(today.weekday())
    past_monday = monday - timedelta(weeks=1)
    past_past_monday = past_monday - timedelta(weeks=1)


    past_week = get_events(name, group, past_monday, past_monday + timedelta(6), filter_by_properties=filter_by, count_by_property=count if len(count) else None).values()[0]
    past_past_week = get_events(name, group, past_past_monday, past_past_monday + timedelta(6), filter_by_properties=filter_by, count_by_property=count if len(count) else None).values()[0]
    total = get_events(name, group, None, None, filter_by_properties=filter_by, count_by_property=count if len(count) else None).values()[0]

    past_week_total = reduce(lambda x,y: x+y, past_week.values(), 0)
    past_past_week_total = reduce(lambda x,y: x+y, past_past_week.values(), 0)
    base = reduce(lambda x,y: x+y, total.values(), 0)
    inc = past_week_total - past_past_week_total
    growth = inc * 1.0 / past_past_week_total

    print past_week_total, past_past_week_total, base, inc, growth

    return base + offset, past_week_total, growth


