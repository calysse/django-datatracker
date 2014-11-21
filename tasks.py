
from celery import task
import operator

import datatracker.conf as conf

if conf.MIXPANEL_FORWARD:
    import mixpanel
    mp = mixpanel.Mixpanel(conf.MIXPANEL_TOKEN)

if conf.INTERCOM_FORWARD:
    from intercom import User


@task
def mp_people_set(user, properties):
    if conf.MIXPANEL_FORWARD and user:
        mp.people_set(user.id, properties)


@task
def mp_track(user, name, properties):
    if conf.MIXPANEL_FORWARD:
        mp.track(user.id if user else 0, name, properties)


def _render_user_report(user_list, output):
    o = open(output + '.csv', 'w+')
    o.write('first_name,last_name,email,profile_url,level,completion,activity,nb_listings\n')
    for item in user_list:
        o.write("%s,%s,%s,https://trampolinn.com/profile-%d,%s,%d%%,%d,%d\n" % (item.first_name.encode('ascii', 'ignore'),
                                                                           item.last_name.encode('ascii', 'ignore'),
                                                                           item.email,
                                                                           item.object.id,
                                                                           item.level_name,
                                                                           item.completion,
                                                                           item.events,
                                                                           item.nb_listings))
    o.close()


def _render_city_report(city_list, output):
    o = open(output + '.csv', 'w+')
    o.write('city,count\n')
    for city, count in city_list:
        if city:
            o.write('%s,%d\n' % (city.encode('ascii', 'ignore'), count))
    o.close()

def _aggregate_events_by(property, events, sortby=1, reverse=True):
    res = {}
    for event in events:
        if event.properties[property] not in res:
            res[event.properties[property]] = 1
        else:
            res[event.properties[property]] += 1

    return sorted(res.items(), key=operator.itemgetter(sortby), reverse=reverse)




@task
def intercom_track(user, name, properties = None):
    if properties is None:
        properties = {}
    if conf.INTERCOM_FORWARD:
        from intercom import Event
        User.create(user_id=user.id)
        Event.create(event_name=name, user_id=user.id, metadata=properties)

@task
def intercom_tags(user, name, tag_or_untag):
    if conf.INTERCOM_FORWARD:
        from intercom import Tag
        print Tag.create(name, tag_or_untag, user_ids=[str(user.id)])
