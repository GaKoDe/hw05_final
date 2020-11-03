import datetime as dt


def year(request):
    now = dt.datetime.now()
    year = now.year
    return {"year": year}
