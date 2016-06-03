WikiTimeline
============
*Last updated: 6/2/16*

WikiTimeline constructs a web-based timeline from a Wikipedia page, using TimelineJS.

General Info
------------

### Team Members

* Aditi Bhandari
* Yixuan Chai
* Will Roever
* Taylor Zheng

### How it Works
WikiTimeline accepts a simple text query and uses the MediaWiki API to parse Wikipedia for events related to that query. It then poplulates a JSON and generates a TimelineJS timeline. 

### Technologies
WikiTimeline is currently running on Heroku at https://wikitimeline.herokuapp.com/. It runs on a Django server.

### How WikiTimeline can be improved
* Add extractors to handle more page structures.
* Implement caching to improve on search times for already-assembled timelines
* Add additional sharing features

Setup
-----

### Setup:

> git clone https://github.com/wroever/wikitimeline
>
> pip install -r requirements.txt

### Running:

> python manage.py collectstatic # Collect static files (if changes made)
>
> python manage.py runserver [PORT] # Will run on localhost:[PORT]
