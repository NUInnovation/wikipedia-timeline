import datetime, time, json, random
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse

from wikitimeline.models import *


"""
Serve index page
"""
@ensure_csrf_cookie
def index(request):
    err = request.GET.get('err','')
    if err == 'noevents':
        msg = 'No events found!'
        context = { 'err': msg }
        return render(request, 'index.html', context)
    else:
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
def timeline(request, id=None):
    if id:
        tl = timeline.objects.get(id=id)
        context = {
            'query': tl.title,
            'timeline': tl.json
        }
        return render(request, 'timeline.html', context)

    raw_query = request.POST.get('validated_query', '')
    if raw_query:
        q = Query(raw_query)
        if not q.is_valid(True):
            raise Exception("Invalid query: " + q.raw_query)
        if not q.page_found():
            raise Exception("Failed to get page: " + q.query)

        events = q.get_events()
        if len(events) < 1:
            return redirect('/?err=noevents')

        title = q.titlefy()

        events_dict = {
            'query': title,
            'titleimg': q.get_title_image(),
            'events': events
        }

        json_obj = render_to_string('json.html', events_dict)
        #tl = Timeline(title=title,json=json_obj)
        #tl.save()
        hexstr = ''.join(random.choice('0123456789abcdef') for n in xrange(8))

        context = {
            'query': title,
            'timeline': json_obj,
            'link': hexstr
        }
    else:  
        return redirect(reverse('homepage'))

    return render(request, 'timeline.html', context)
