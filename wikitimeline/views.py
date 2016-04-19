import datetime, time, json
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from wikitimeline.models import *

"""
Serve index page
"""
@ensure_csrf_cookie
def index(request):
    return render(request, 'index.html', {'current_date': datetime.datetime.now()})

"""
Generate a JSON-formatted timeline from the given query
"""
def timeline(request):
    context = { 'query': request.POST.get('query', '') }
    return render(request, 'timeline.html', context)

"""
Load "On this day in history"
"""
def loading(request):
    tz = request.POST.get('timezone', 0)
    q = ThisDayQuery(tz)
    events = q.get_events()
    return render(request, 'loading.html', {'events': events})