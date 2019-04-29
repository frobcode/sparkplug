from sparkplug.timereporters.base import mn_md_mx
from datetime import timedelta

def test_timereporer_min():
    testdata = [timedelta(seconds=x) for x in (5,3,1,6,8,9,5,3)]
    mn, md, mx = mn_md_mx(testdata)
    assert timedelta(seconds=1).total_seconds() * 1000 == mn

def test_timereporer_median_even_count():
    testdata = [timedelta(hours=x) for x in (6,1,7,0,4,2,9,7)]
    mn, md, mx = mn_md_mx(testdata)
    assert timedelta(hours=5).total_seconds() * 1000 == md

def test_timereporer_median_odd_count():
    testdata = [timedelta(minutes=x) for x in (6,2,7,0,5)]
    mn, md, mx = mn_md_mx(testdata)
    assert timedelta(minutes=5).total_seconds() * 1000 == md

def test_timereporer_max():
    testdata = [timedelta(seconds=x) for x in (1,8,3,9,4,2,8)]
    mn, md, mx = mn_md_mx(testdata)
    assert timedelta(seconds=9).total_seconds() * 1000 == mx
