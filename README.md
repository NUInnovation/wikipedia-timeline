WikiTimeline
============
*Last updated: 5/9/16*

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

### Next Steps
* Improve on MediaWiki parsing, handle different page structures.
* Incorporate images.
* Front-end improvements (improving instructional language and error feedback).

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
