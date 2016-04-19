#!/usr/bin/python
# -*- coding: utf-8 -*-

# from django.db import models # MIGHT NOT NEED

import json, pycurl, re, requests, mwparserfromhell, datetime
from StringIO import StringIO

API_URL = "https://en.wikipedia.org/w/api.php"
# Source for below: http://daringfireball.net/2010/07/improved_regex_for_matching_urls
RX_URLMATCH = r'(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))'
RX_WIKIURL = r'wikipedia\.org/wiki/(.+)'
RX_ANNIVERSARIES = ur'\|([\s]*)?\[\[([0-9]+)\]\](.*)'
ANNIVERSARIES = 'Wikipedia:Selected_anniversaries'

def mw2plaintext(mkp):
    RXs = [ur"\u2013",r"\|.+?\]{2}",r"\<\!\-\-.+?\-\-\>",r"\'{3}",r"\[{2}",r"\]{2}"]
    txt = mkp
    for r in RXs:
        txt = re.sub(r,'',txt)
    return txt.strip()

class Query(object):

    curl_response = None
    _errors = {}

    def __init__(self, raw):
        self.raw_query = raw

    def validate(self):
        if not self.raw_query:
            self._errors['validation'] = 'Query cannot be empty'
            return None
        if re.search(RX_URLMATCH, self.raw_query):
            # Query is a link (note that this allows for use of URL shorteners or other obfuscated links)
            # Do a quick Curl to verify the page actually exists
            buffer = StringIO()
            c = pycurl.Curl()
            c.setopt(pycurl.URL, self.raw_query)
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.setopt(pycurl.WRITEDATA, buffer)
            try:
                c.perform()
                status = c.getinfo(pycurl.HTTP_CODE)
                effective_url = c.getinfo(pycurl.EFFECTIVE_URL)
                # Confirm the link is well-formed and the page is valid.
                wiki_url_scan = re.search(RX_WIKIURL, effective_url)
                if status == 200 and wiki_url_scan:
                    self.query = wiki_url_scan.groups()[0]
                    self.html_markup = buffer.getvalue()
                    return self.query
            except:
                pass
            self._errors['validation'] = 'Link is not a valid Wikipedia link!'
            return None
        else:
            # Query is simple text
            self.query = self.raw_query
            return self.query

    def is_valid(self):
        self.validate()
        return hasattr(self, 'query')

    def parse(self):
        data = {"action": "query", "prop": "revisions", "rvlimit": 1,
                "rvprop": "content", "format": "json", "titles": self.query}
        resp = requests.get(API_URL, params=data)
        res = resp.json()
        text = res["query"]["pages"].values()[0]["revisions"][0]["*"]
        self.markup = mwparserfromhell.parse(text).__unicode__()

class ThisDayQuery(Query):
    def __init__(self, timezone):
        try:
            now = datetime.datetime.now() - datetime.timedelta(hours=   int(timezone))
        except TypeError:
            raise Exception("Invalid timezone value!")
        datestr = now.strftime('%B_%-d')
        self.raw_query = '%s/%s' % (ANNIVERSARIES, datestr)

    def get_events(self):
        if not self.is_valid():
            # Always true, unless Wikipedia changes main page url
            raise Exception('Invalid link!') 
        self.parse()
        raw_events = re.findall(RX_ANNIVERSARIES, self.markup)
        events = []
        for e in raw_events:
            events.append({
                'year': e[1].strip(),
                'description': mw2plaintext(e[2])
            })
        return events




