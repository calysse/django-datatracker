from rest_framework.decorators import api_view
import datatracker.models as model
from django.http import HttpResponse
from django.db.models import Count
from datetime import date, datetime, timedelta
import operator
import data

import datatracker.conf as conf

def _csv_response(matrix):
    res = map(lambda x: ','.join(map(unicode, x)), matrix)
    response = HttpResponse(content_type='plain/text')
    response.write("\n".join(res))
    return response

def _append_param(param, key, GET, res):
    if key in GET:
        res.append([param] + GET[key].split(','))

def _add_custom_cyfe_parameters(GET, res):
    # Add custom Cyfe parameters
    for item in GET:
        if item.startswith('Cy_'):
            _append_param(item.replace('Cy_', ''), item, GET, res)


DATA_FUNCTIONS = data.DATA_FUNC

def stats(request, func):
    return _csv_response(DATA_FUNCTIONS[func]())



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


#
# https://trampolinn.com/fr/datatrack/cohort/?main_metric=Member%20activity,,&trigger_metric=Member%20activity,,&name=User&granularity=month&nb_items=10
#
def cohort(request):
    main_metric = request.GET.get('main_metric')
    trigger_metric = request.GET.get('trigger_metric')
    granularity = request.GET.get('granularity', 'week')
    nb_items = int(request.GET.get('nb_items', '12'))
    name = request.GET.get('name', 'metric')

    res = [[granularity.capitalize(), name.capitalize()] + [str(i) for i in range(1, nb_items + 1)]]
    res.extend(data.cohorts(main_metric, trigger_metric, granularity=granularity, nb_items=nb_items))

    _add_custom_cyfe_parameters(request.GET, res)

    return _csv_response(res)


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


# Example: data/event?start=20140901&end=20141010&agg_by=date&sort_by=-0&&metric=Acquisition,Invite sent,City:Paris,Nb invite&formula=Acquisition,Member aquired

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
