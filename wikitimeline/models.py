#!/usr/bin/python
# -*- coding: utf-8 -*-

# from django.db import models # MIGHT NOT NEED

import json, pycurl, re, requests, mwparserfromhell, datetime, HTMLParser, wikipedia
from StringIO import StringIO
from bs4 import BeautifulSoup

API_URL = "https://en.wikipedia.org/w/api.php"
# Source for below: http://daringfireball.net/2010/07/improved_regex_for_matching_urls
RX_URLMATCH = r'(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))'
URL_PREFIX_EN = 'https://en.wikipedia.org'
RX_WIKIURL = r'wikipedia\.org/wiki/(.+)'
RX_DATES = ur'\=\=\= ([0-9]+) \=\=\=[\r\n](\<\!\-\-.*\-\-\>[\r\n])?(?:(\* .+[\r\n])?)+'
ANNIVERSARIES = 'Wikipedia:selected anniversaries'
RX_ANNIVERSARIES = ur'([0-9]+) (–|-) (.*)'

def mw2plaintext(mkp):
    RXs = [ur"\u2013",r"\|.+?\]{2}",r"\<\!\-\-.+?\-\-\>",r"\'{3}",r"\[{2}",r"\]{2}"]
    txt = mkp
    for r in RXs:
        txt = re.sub(r,'',txt)
    h = HTMLParser.HTMLParser()
    return h.unescape(txt.strip())

class Query(object):

    feedback = {}
    # Maybe need the below for wikipedia python API
    #_opts = {
    #    'action': 'query',
    #    'prop': 'revisions',
    #    'rvlimit': 1,
    #    'rvprop': 'content',
    #    'format': 'json',
    #}
    #_base_url= 'https://en.wikipedia.org/w/api.php?'
    #######

    def __init__(self, raw):
        self.raw_query = raw

    def validate(self, get_markup=False):
        if not self.raw_query:
            self.feedback['error'] = 'Query cannot be empty'
            return
        if re.search(RX_URLMATCH, self.raw_query):
            # Query is a link (note that this allows for use of URL shorteners or other obfuscated links)
            # Do a quick Curl to verify the page actually exists and is legimate
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
                    if get_markup: self.markup = buffer.getvalue()
                    return
            except:
                pass
            self.feedback['error'] = 'Link is not a valid Wikipedia link!'
        else:
            result = wikipedia.search(self.raw_query, suggestion=True)
            print result
            if result[0] and result[0][0] and result[0][0].lower() == self.raw_query.lower():
                # Best case scenario... exact match
                print "Query accepted: " + self.raw_query
                self.query = self.raw_query
            elif result[1]:
                # Use the first suggestion
                print "No matching page identified. Using suggestion: " + result[1]
                self.query = result[1]
            elif result[0]:
                # Display suggestions
                print "No matching page found and no suggestion was provided. Displaying potential alternatives:\n" + ''.join([("\t%s\n" % s) for s in result[0]])
                self.feedback['lead'] = "Whoops, nothing found."
                self.feedback['clarification'] = "Did you mean to search for one of the items below?"
                self.feedback['suggestions'] = result[0]
            else:
                # We got nothing...
                print "No matching page found, and no suggestions are available."
                self.feedback['lead'] = "Whoops, nothing found."
                self.feedback['error'] = "Please check that you've spelled your query correctly and try again. "\
                                         "You may find it easier to copy a link directly to the page you wish to summarize."

            if hasattr(self, 'query'):
                try:
                    page = wikipedia.page(self.query)
                    if get_markup:
                        self.markup = page.html()
                except wikipedia.exceptions.DisambiguationError as e:
                    print e
                    self.feedback['lead'] = "Disambiguation:"
                    self.feedback['clarification'] = "Did you mean to search for one of the items below?"
                    self.feedback['suggestions'] = e.options

    def is_valid(self, get_markup=False):
        self.validate(get_markup)
        return hasattr(self, 'query')

    def page_found(self):
        return hasattr(self, 'markup')

    def eval_structure(self):
        return  

    def get_events(self):
        soup = BeautifulSoup(self.markup, 'html.parser')

        # Format 1: see 'List of Catholic Saints'
        links = soup.find_all('span', {'class' : 'mw-headline'})
        
        events = []
        for link in links:
            maybe_year = link.get_text().strip()
            if not re.match(r'[0-9]+$', maybe_year):
                continue
            year = maybe_year
            # Check for multiple events
            events_mkp = link.parent.find_next('ul').find_all('li')
            for e in events_mkp:
                media_url = None
                first_anchor = e.a
                if first_anchor:
                    ext_href = first_anchor.get('href', None)
                    if ext_href and ext_href.startswith('/wiki/'):
                        media_url = URL_PREFIX_EN + ext_href
                desc = e.get_text().strip()
                events.append({
                    'year': year,
                    'description': desc,
                    'media_url': media_url
                })
        return events


class ThisDayQuery(Query):
    def __init__(self, timezone):
        try:
            now = datetime.datetime.now() - datetime.timedelta(hours=int(timezone))
        except TypeError:
            raise Exception("Invalid timezone value!")
        daystr = now.strftime('%d')
        datestr = now.strftime('%B ').lower() + str(int(daystr))
        # Set validated query and markup - no further validation required
        self.query = '%s %s' % (ANNIVERSARIES, datestr)
        self.markup = wikipedia.page(self.query).html()

    def get_events(self):

        soup = BeautifulSoup(self.markup, 'html.parser')
        links = soup.find_all("a", {"title" : lambda t: t and re.match(r'[0-9]+$',t)})
        
        events = []
        for link in links:
            desc = link.parent.get_text().strip()
            rxres = re.match(RX_ANNIVERSARIES,desc,re.UNICODE)
            try:
                groups = rxres.groups()
                events.append({
                    'year': groups[0],
                    'description': groups[2]
                })
            except:
                pass
        return events

