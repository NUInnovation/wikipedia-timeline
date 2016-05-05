import datetime, time, json
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.csrf import ensure_csrf_cookie

from wikitimeline.models import *


"""
Serve index page
"""
@ensure_csrf_cookie
def index(request):
    return render(request, 'index.html')

"""
Validate query, return JSON-formatted feedback or events
"""
def validate(request):
    raw_query = request.POST.get('query', '')
    q = Query(raw_query)

    if not q.is_valid():
        err_html = render_to_string('feedback.html', q.feedback)
        return JsonResponse({'is_valid': False, 'err_html': err_html})

    """
    Load "On this day in history"
    """
    tz = request.POST.get('timezone', 0)
    tdq = ThisDayQuery(tz)
    events = tdq.get_events()
    events_dict = { 'events': events }
    context = {'is_valid': True, 'validated_query': q.query, 'events_html': render_to_string('thisdayinhist.html', events_dict) }
    return JsonResponse(context)


"""
Generate a JSON-formatted timeline from the given query
"""
def timeline(request):
    raw_query = request.POST.get('validated_query', '')
    q = Query(raw_query)
    if not q.is_valid(True):
        raise Exception("Invalid query: " + q.raw_query)
    if not q.page_found():
        raise Exception("Failed to get page: " + q.query)

    events = q.get_events()
    events_dict = { 'query': q.query, 'events': events }
    context = { 'query': q.query, 'timeline': render_to_string('json.html', events_dict) }
    
    # Get events!
    return render(request, 'timeline.html', context)
