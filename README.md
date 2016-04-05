WikiTimeline constructs a web-based timeline from a Wikipedia page, using TimelineJS.

To set up:

1) git clone https://github.com/wroever/wikitimeline
2) pip install -r requirements.txt

To run:

1) python manage.py collectstatic # Collect static files (if changes made)
2) python manage.py runserver [PORT] # Will run on localhost:[PORT]
