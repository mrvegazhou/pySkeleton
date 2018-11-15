# -*- coding: utf-8 -*-'''
from math import sqrt, log
from datetime import datetime, timedelta
import time

'''
威尔逊区间算法
'''
def _confidence(ups, downs):
    n = ups + downs
    if n == 0:
        return 0
    z = 1.281551565545  # 80% confidence
    p = float(ups) / n
    left = p + 1/(2*n)*z*z
    right = z*sqrt(p*(1-p)/n + z*z/(4*n*n))
    under = 1+1/n*z*z
    return (left - right) / under

up_range = 400
down_range = 100
_confidences = []
for ups in xrange(up_range):
    for downs in xrange(down_range):
        _confidences.append(_confidence(ups, downs))

def confidence(ups, downs):
    if ups + downs == 0:
        return 0
    elif ups < up_range and downs < down_range:
        return round(_confidences[downs + ups * down_range], 6)*1000000
    else:
        return round(_confidence(ups, downs), 6)*1000000

###############################################################################
epoch = datetime(1970, 1, 1)
def epochSeconds(date):
    td = date - epoch
    return td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)

def score(ups, downs):
    return ups - downs

def hot(ups, date, fans):
    s = score(ups, 0)
    order = log(max(s, 1), 10)
    fans = log(fans, 10) + 1
    seconds = epochSeconds(date) - time.mktime(time.strptime("2016-05-01", '%Y-%m-%d'))
    return round(order + seconds/45000)
