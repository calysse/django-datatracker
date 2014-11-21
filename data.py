__author__ = 'sebastienclaeys'

#####################
# User Segmentation
#####################

from haystack.query import SearchQuerySet, SQ
import acasa.models as model
import operator
from datetime import datetime, date, timedelta

def get_facet(table, field):
    tables = {'User': model.User,
              'Listing': model.Listing,
              'City': model.City,
              'Project': model.Project}

    sqs = SearchQuerySet().models(tables[table]).facet(field)
    return dict(sqs.facet_counts()['fields'][field])


def get_by_field(table, field):
    tables = {'User': model.User,
              'Listing': model.Listing,
              'City': model.City,
              'Project': model.Project}
    sqs = SearchQuerySet().models(tables[table]).all()
    res = {}
    for i in sqs:
        n = i.name.encode('ascii', 'ignore').lower()
        if not n in res:
            res[n] = 0
        res[n] += i.__dict__[field]
    return res

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
    import data_tracker.models as dt_model
    from datetime import datetime, timedelta

    if start is not None and end is not None:
        dstart = datetime.strptime(start, '%Y%m%d') if type(start) in [str, unicode] else start
        dend = (datetime.strptime(end, '%Y%m%d') if type(end) in [str, unicode] else end) + timedelta(1)
        events = dt_model.Event.objects.filter(datetime__range=[dstart, dend]).order_by('-datetime')
    else:
        events = dt_model.Event.objects.all().order_by('-datetime')

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

        if aggregate_by == None: # Default, aggregate by date
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
        else:
            # Counting by properties
            res[cat_key][key] += event.properties[count_by_property]

    return res
    #return sorted(res.items(), key=operator.itemgetter(int(sortby)), reverse=(sortby[0] == '-'))



def scan_metric(group, name, filter_by, count, offset):
    today = date.today()
    monday = today - timedelta(today.weekday())
    past_monday = monday - timedelta(weeks=1)
    past_past_monday = past_monday - timedelta(weeks=1)


    past_week = get_events(name, group, past_monday, past_monday + timedelta(6), filter_by_properties=filter_by, aggregate_by_property=None, count_by_property=count if len(count) else None).values()[0]
    past_past_week = get_events(name, group, past_past_monday, past_past_monday + timedelta(6), filter_by_properties=filter_by, aggregate_by_property=None, count_by_property=count if len(count) else None).values()[0]
    total = get_events(name, group, None, None, filter_by_properties=filter_by, aggregate_by_property=None, count_by_property=count if len(count) else None).values()[0]

    past_week_total = reduce(lambda x,y: x+y, past_week.values(), 0)
    past_past_week_total = reduce(lambda x,y: x+y, past_past_week.values(), 0)
    base = reduce(lambda x,y: x+y, total.values(), 0)
    inc = past_week_total - past_past_week_total
    growth = inc * 1.0 / past_past_week_total

    print past_week_total, past_past_week_total, base, inc, growth

    return base + offset, past_week_total, growth


from common.decorators import cached_function
from datetime import datetime, date, timedelta
month_3 = date.today() - timedelta(weeks=12)
month_5 = date.today() - timedelta(weeks=4*5)
month = date.today() - timedelta(weeks=4)
month_2 = date.today() - timedelta(weeks=8)
week = date.today() - timedelta(12)


@cached_function(60 * 60)
def global_numbers():
    nb_users = len(model.User.objects.all())
    facets = SearchQuerySet().models(model.User).facet('nb_listings').facet('nb_groups').facet('nb_friends').facet('nb_projects').facet_counts()
    nb_parrains = len(model.User.objects.annotate(scount=model.models.Count('sponsored')).filter(scount__gt=0))
    nb_fileul = len(model.UserProfile.objects.filter(sponsor__isnull=False))
    nb_listings = len(model.Listing.objects.all())
    nb_active = len(model.Listing.objects.filter(active=True))
    nb_projects = len(model.Project.objects.all())
    nb_booking = len(model.Contract.objects.all())
    friends_per_user = round(float(reduce(lambda x, y: x+ y[0] * y[1], facets['fields']['nb_friends'], 0)) / float(nb_users), 2)
    group_per_user = round(float(reduce(lambda x, y: x+ y[0] * y[1], facets['fields']['nb_groups'], 0)) / float(nb_users), 2)
    nb_cities = len(set(map(lambda x: x.name, model.City.objects.all())))
    nb_countries = len(set(map(lambda x: x.name, model.Country.objects.all())))

    return [['Nb Users', 'Nb parrains', 'Nb fileul', 'Nb Listings', 'Active listings', 'Nb Projects', 'Nb Bookings', 'Friends/User', 'Group/User', 'Nb cities', 'Nb countries'],
           [nb_users, nb_parrains, nb_fileul, nb_listings, nb_active, nb_projects, nb_booking, friends_per_user, group_per_user, nb_cities, nb_countries]]

def user_numbers():
    facets = SearchQuerySet().models(model.User).facet('nb_listings').facet('nb_groups').facet('nb_friends').facet('nb_projects').facet_counts()
    nb_users = len(model.User.objects.all())
    listings_per_user = round(float(reduce(lambda x, y: x+ y[0] * y[1], facets['fields']['nb_listings'], 0)) / float(nb_users), 2)
    projects_per_user = round(float(reduce(lambda x, y: x+ y[0] * y[1], facets['fields']['nb_projects'], 0)) / float(nb_users), 2)
    group_per_user = round(float(reduce(lambda x, y: x+ y[0] * y[1], facets['fields']['nb_groups'], 0)) / float(nb_users), 2)
    friends_per_user = round(float(reduce(lambda x, y: x+ y[0] * y[1], facets['fields']['nb_friends'], 0)) / float(nb_users), 2)
    return [['Listing /U', 'Projects /U', 'Groups /U', 'Friends /U'],
           [listings_per_user, projects_per_user, group_per_user, friends_per_user]]



