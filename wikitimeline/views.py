import datetime, time, json
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from wikitimeline.models import *

"""
Serve index page
"""
def index(request):
    return render(request, 'index.html', {'current_date': datetime.datetime.now()})

"""
Generate a JSON-formatted timeline from the given query
"""
@ensure_csrf_cookie
def timeline(request):
    time.sleep(10) # Sleep to simulate processing time for more complicated timelines
    context = { 'query': request.POST.get('query', ''), 'message': 'huzzah, ajax request received!' }
    return render(request, 'timeline.html', context)

"""
Load "On this day in history"
"""
def loading(request):
    q = ThisDayQuery()
    events = q.get_events()
    return render(request, 'loading.html', {'events': events})