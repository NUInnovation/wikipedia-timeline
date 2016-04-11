from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
import datetime # not really using this...

def index(request):
    now = datetime.datetime.now()
    t = get_template('index.html')
    html = t.render(Context({'current_date': now}))
    return HttpResponse(html)