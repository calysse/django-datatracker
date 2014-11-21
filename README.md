Data tracker
==========

## Settings

In settings.py:

       MIXPANEL_FORWARD = False
       INTERCOM_FORWARD = False


## Event data api

Usage

    base URL = datatrack/gevents
    Params:
    start=YYYYMMDD
    end=YYYYMMDD
    metric=group,name,property_filter,property_name
    formula=group,name,property_filter,property_name
      property_filter=key:val
    agg_by=property_name
    sort_by=[-]idx


Example

    datatrack/gevents/?start=20140901&end=20141010&metric=,Marketing%20click,origin:Invite,
    datatrack/gevents/?start=20140901&end=20141010&metric=,Marketing click,,&agg_by=origin&reversed=1
    datatrack/gevents/?start=20140901&end=20141010&formula=,Marketing%20click,origin:Invite,&metric=,Member%20acquired,,&metric=,Marketing%20click,,