WikiTimeline constructs a web-based timeline from a Wikipedia page, using TimelineJS.

To set up:

git clone https://github.com/wroever/wikitimeline
pip install -r requirements.txt

To run:

./manage.py collectstatic # Collect static files (if changes made)
./manage.py runserver [PORT] # Will run on localhost:[PORT]
