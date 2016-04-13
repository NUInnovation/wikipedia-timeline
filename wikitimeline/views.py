import datetime # not really using this...
from django.shortcuts import render

def index(request):
    return render(request, 'index.html', {'current_date': datetime.datetime.now()})