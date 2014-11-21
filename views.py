from rest_framework.decorators import api_view
import acasa.models as acasa_model
import ab.models as ab_model
import data_tracker.models as model
from django.http import HttpResponse
from django.db.models import Count
import data
from datetime import date, datetime, timedelta
import operator

def _csv_response(matrix):
    res = map(lambda x: ','.join(map(unicode, x)), matrix)
    return HttpResponse("\n".join(res))


def ab_exp_status(request, id):
    exp = ab_model.Experiment.objects.get(pk=int(id))
    res = [[x.template_name for x in exp.test_set.all()],
           [((x.conversions * 100) / x.hits) if x.hits else 0 for x in exp.test_set.all()]
    ]
    return _csv_response(res)


def _append_param(param, key, GET, res):
    if key in GET:
        res.append([param] + GET[key].split(','))


def _add_custom_cyfe_parameters(GET, res):
    # Add custom Cyfe parameters
    for item in GET:
        if item.startswith('Cy_'):
            _append_param(item.replace('Cy_', ''), item, GET, res)



def user_target(request, target):
    nb = len(acasa_model.User.objects.all())
    res = [["Members", "Target"],
           [nb, int(target)]
    ]
    return _csv_response(res)


def user_acquired(request):
    daily_report = acasa_model.User.objects.extra(select={'day': 'date(date_joined)'}).values('day').annotate(new_members=Count('id'))
    res = [['Date', 'New members']] + [[x['day'].strftime("%Y%m%d"), x['new_members']] for x in daily_report]
    return _csv_response(res)


DATA_FUNCTIONS = data.__dict__

def user_segmentation(request, facet):
    return _csv_response(DATA_FUNCTIONS[facet]())

def stats(request, func):
    return _csv_response(DATA_FUNCTIONS[func]())



####
# New GENERIC Views
####
def esdata(request, dtype, table, filter):
    # Get usable data from search enfine
    if dtype == 'facet':
        segments = data.get_facet(table, filter)
    elif dtype == 'field':
        segments = data.get_by_field(table, filter)
    else:
        raise Exception("Unrecognized data type")


    # Exclude some keys if needed
    for key in request.GET.getlist('exclude_key', []):
        if key in segments:
            del segments[key]
        elif int(key) in segments:
            del segments[int(key)]

    # Exclude some keys if needed
    for val in request.GET.getlist('exclude_val', []):
        for key in segments.keys():
            if segments[key] <= int(val):
                del segments[key]


    # Sort if required
    if 'sortval' in request.GET:
        reverse = False
        if request.GET['sortval'] == '-1':
            reverse = True
        ssegments = sorted(segments.items(), key=operator.itemgetter(1), reverse=reverse)
    elif 'sortkey' in request.GET:
        reverse = False
        if request.GET['sortkey'] == '-1':
            reverse = True
        ssegments = sorted(segments.items(), reverse=reverse)
    else:
        ssegments = segments.items()

    # Limit the list size
    if 'limit' in request.GET:
        ssegments = ssegments[int(request.GET['limit'])]

    # Generete the final data
    if 'reversed' in request.GET:
        res = [map(operator.itemgetter(0), ssegments),
               map(operator.itemgetter(1), ssegments)]
    else:
        if dtype == 'facet':
            # Facet special case where the filter become the key
            res = [[filter, table]]
        else:
            res = [[table, filter]]

        for key, val in ssegments:
            res.append([key, val])


    _add_custom_cyfe_parameters(request.GET, res)

    return _csv_response(res)


def _get_metric(metric, start, end, agg_by):
    override_name = None
    mtuple = metric.split(',')
    if len(mtuple) == 5:
        group, name, filter_by, count, override_name = mtuple
    else:
        group, name, filter_by, count = mtuple
    if len(filter_by):
        filter_by = {x[0]: x[1] for x in map(lambda y: y.split(':'), filter_by.split(';'))}
        print "Filtering by: " + str(filter_by)
    return data.get_events(name, group, start, end, filter_by_properties=filter_by, aggregate_by=agg_by, count_by_property=count if len(count) else None, override_name=override_name).items()


# Pivot metrics matrix
# Input = [ ['Invite sent', {'20141008': 10, '20141009', 20}],
#           ['Member acquired', {'20141008': 150, '20141009', 145}],
#         ]
# Output = [ ['20141008', 10, 150]
#            ['20141009', 20, 140]
#          ]

def _pivot_metrics(metrics, formulas, sortby="0"):
    res = {}
    for i in range(len(metrics)):
        formula = None
        if i < len(formulas):
            formula = formulas[i][1]
        metric = metrics[i][1]
        for key in metric:
            if key not in res:
                res[key] = []

            for y in range(len(res[key]), i):
                res[key].append(0)

            if formula:
                if not key in formula or formula[key] == 0:
                    # Skip if we can't proceed with the formula
                    continue
                else:
                    res[key].append(round(float(100 * metric[key]) / float(formula[key]), 1))
            else:
                res[key].append(metric[key])

    return sorted(map(lambda x: [x[0]] + x[1], res.items()), key=operator.itemgetter(int(sortby)), reverse=(sortby[0] == '-'))



def compare_weeks(request):
    metrics = []

    sum = request.GET.get('sum', False)

    group, name, filter_by, count = request.GET['metric'].split(',')
    today = date.today()
    monday = today - timedelta(today.weekday())
    past_sunday = (monday - timedelta(1)).strftime("%Y%m%d")
    past_monday = (monday - timedelta(weeks=1)).strftime("%Y%m%d")
    monday = monday.strftime("%Y%m%d")
    today = today.strftime("%Y%m%d")

    metrics.extend([data.get_events(name, group, past_monday, past_sunday, filter_by_properties=filter_by, aggregate_by=None, count_by_property=count if len(count) else None).values()[0],
                    data.get_events(name, group, monday, today, filter_by_properties=filter_by, aggregate_by=None, count_by_property=count if len(count) else None).values()[0]
                    ])

    result = [["Day of week", "Past week", "Current week"]]

    res = {}
    for metric in metrics:
        for datekey, val in metric.items():
            dt = datetime.strptime(datekey, '%Y%m%d')
            key = "%d_%s" % (dt.weekday(), dt.strftime('%A'))
            if key not in res:
                res[key] = []
            res[key].append(val)

    result.extend(sorted(map(lambda x: [x[0]] + x[1], res.items()), key=operator.itemgetter(0)))

    if sum == 'True':
        for i in range(len(metrics)):
            sum = 0
            for y in range(len(result)):
                if len(result[y]) > i+1:
                    if type(result[y][i+1]) in [float, int]:
                        sum += result[y][i+1]
                        result[y][i+1] = sum

    _add_custom_cyfe_parameters(request.GET, result)

    return _csv_response(result)


def prevision(request):
    metrics = request.GET.getlist('metric', [])
    to_date_str = request.GET['date']
    to_date = datetime.strptime(to_date_str, "%Y%m%d").date()
    today = date.today()
    week = timedelta(weeks=1)

    # Monday to monday
    start = today - timedelta(today.weekday())
    end = to_date - timedelta(to_date.weekday())

    result = [["Week"]]
    res = {}
    for metric in metrics:
        group, name, filter_by, count, offset = metric.split(',')
        result[0].append(name)
        base, inc, growth = data.scan_metric(group, name, filter_by, count, int(offset))
        edate = start

        while edate <= end:
            key = edate.strftime("%Y%m%d")
            if key not in res:
                res[key] = []
            res[key].append(base)

            # Compute current week growth
            inc = int(inc + (growth * inc))
            base = base + inc
            edate = edate + week

    result.extend(sorted(map(lambda x: [x[0]] + x[1], res.items()), key=operator.itemgetter(0)))
    _add_custom_cyfe_parameters(request.GET, result)
    return _csv_response(result)


# Example: data/event?start=20140901&end=20141010&agg_by=date&sortby=-0&&metric=Acquisition,Invite sent,City:Paris,Nb invite&formula=Acquisition,Member aquired
def events_gen(request):
    agg_by = request.GET.get('agg_by', None)
    sort_by = request.GET.get('sort_by', '0')
    start = request.GET.get('start')
    end = request.GET.get('end')
    sum = request.GET.get('sum', False)

    metrics = []
    formulas = []
    for metric in request.GET.getlist('metric', []):
        metrics.extend(_get_metric(metric, start, end, agg_by))
    for metric in request.GET.getlist('formula', []):
        formulas.extend(_get_metric(metric, start, end, agg_by))

    print metrics

    # Generete the final data
    if 'reversed' in request.GET:
        # if reversed data is requested, only valid for one metric
        res = [map(operator.itemgetter(0), metrics[0][1].items()),
               map(operator.itemgetter(1), metrics[0][1].items())]
    else:
        # build metric list
        mnames = []
        for i in range(len(metrics)):
            if i < len(formulas):
                mnames.append("%s / %s(%%)" % (metrics[i][0], formulas[i][0]))
            else:
                 mnames.append(metrics[i][0])

        res = [[agg_by if agg_by is not None else "Date"] + mnames]

        res.extend(_pivot_metrics(metrics, formulas, sort_by))


    if sum == 'True':
        for i in range(len(mnames)):
            sum = 0
            for y in range(len(res)):
                if len(res[y]) > i+1:
                    if type(res[y][i+1]) in [float, int]:
                        sum += res[y][i+1]
                        res[y][i+1] = sum


    _add_custom_cyfe_parameters(request.GET, res)

    return _csv_response(res)

# params:
# start=YYYYMMDD
# end=YYYMMDD
# name=<event name>
# Example:
#   http://trampolinn.com/datatrack/events/?start=20140920&end=20140930&name=Member%20acquired&name=Listing%20created
def events(request):
    names = request.GET['names'].split(',')
    evs = model.Event.objects.retrieve(request.GET, names)

    print evs
    for e in evs:
        print e.name, str(e.datetime)

    tmp = {}
    # First pass, aggregate daily count
    for event in evs:
        dt = event.datetime.strftime('%Y%m%d')
        if not dt in tmp:
            tmp[dt] = {}
        if not event.name in tmp[dt]:
            tmp[dt][event.name] = 0

        tmp[dt][event.name] = tmp[dt][event.name] + 1

    res = [['Date'] + names]

    # Second pass, build the result dict in Cyfe format
    for date in sorted(tmp):
        ev_list = []
        ev_dict = tmp[date]
        for name in names:
            if not name in ev_dict:
                ev_list.append(0)
            else:
                ev_list.append(ev_dict[name])
        res.append([date] + ev_list)


    _add_custom_cyfe_parameters(request.GET, res)


    return _csv_response(res)
