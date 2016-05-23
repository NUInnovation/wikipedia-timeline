#!/usr/bin/python
# -*- coding: utf-8 -*-

# from django.db import models # MIGHT NOT NEED

import json, pycurl, re, requests, datetime, HTMLParser, wikipedia
from StringIO import StringIO
from bs4 import BeautifulSoup
from urllib import unquote

# Source for below: http://daringfireball.net/2010/07/improved_regex_for_matching_urls
RX_URLMATCH = r'(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))'
URL_PREFIX_EN = 'https://en.wikipedia.org'
RX_WIKIURL = r'wikipedia\.org/wiki/(.+)'
RX_DATES = ur'\=\=\= ([0-9]+) \=\=\=[\r\n](\<\!\-\-.*\-\-\>[\r\n])?(?:(\* .+[\r\n])?)+'
ANNIVERSARIES = 'Wikipedia:selected anniversaries'
RX_ANNIVERSARIES = ur'([0-9]+) (–|-) (.*)'

"""
EventExtractor - base extractor object declaration, format-specific extractors inherit from this
"""
class EventExtractor(object):
    def __init__(self, soup):
        self.soup = soup

    def stripRefs(self,txt):
        txt = txt.strip()
        RX = '\[[0-9]+\]'
        return re.sub(RX,'',txt)

    def getLeadImageFromPage(self,page_id):
        #image = 'https://en.wikipedia.org/w/api.php?action=parse&text={{%s}}&prop=images' % page_id
        wp_image_query = 'https://en.wikipedia.org/w/api.php?action=query&titles=%s&prop=pageimages&pilimit=1&format=json' % page_id

        # Curl dat image URL
        buffer = StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, wp_image_query)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.WRITEDATA, buffer)
        try:
            c.perform()
            status = c.getinfo(pycurl.HTTP_CODE)
            if status == 200:
                print buffer.getvalue()
                curl_result = json.loads(buffer.getvalue())
                pages = curl_result['query']['pages']
                d = pages.items()
                wp_pagenum = d[0][0]
                thumbsrc = pages[wp_pagenum]['thumbnail']['source']
                #image_loc = 'https://commons.wikimedia.org/w/api.php?action=query&titles=File:%s&prop=imageinfo&&iiprop=url&iiurlwidth=220'
                # The below is a hacky way to get around doing an extra API query to locate the image
                rx_thumbsrc_match = re.match(r'(.*)/[0-9]+px\-.+$',thumbsrc)
                if rx_thumbsrc_match:
                    image_src = rx_thumbsrc_match.groups()[0]
                    image_src = re.sub('/thumb/','/',image_src)
                    return image_src
        except:
            print "No image found for page: " + page_id
        return None 

    def getYearRange(self,raw_txt):
        # Check for BCE dates
        range_split = re.search(ur'([0-9,]+(\sBC(E)?)?)?\s?(to|–|-)?\s?([0-9,]+(\sBC(E)?)?)?',raw_txt,re.UNICODE)
        # Produces something like: (None, None, None, 'to', '14,000 BCE', ' BCE', 'E')
        if range_split:
            groups = range_split.groups()
            raw_start = groups[0]
            raw_end = groups[4]
            rx_digits = r'[^0-9]'
            if groups[3]:
                # We have a range
                endyr = re.sub(rx_digits,'',raw_end) if raw_end else datetime.datetime.now().strftime('%Y')
                # Kind of a hacky solution here to prevent scale distortion
                startyr = re.sub(rx_digits,'',raw_start) if raw_start else endyr
                if groups[5]:
                    # Both start and end must be negative...
                    return '-'+startyr, '-'+endyr
                elif groups[1]:
                    return '-'+startyr, endyr
            else:
                startyr = re.sub(rx_digits,'',raw_start)
                endyr = startyr
                if groups[1]:
                    return '-'+startyr, '-'+endyr
            return startyr, endyr
        else:
            print "Failed to split year range: " + raw_txt
            return '',''
        
        
class EventExtractorAnniv(EventExtractor):
    """
    'Anniversary' format: See 'Wikipedia: selected anniversaries jan 1'
    """
    def extract(self, append_to=list(), maxevents=None, get_images=True):
        events = append_to
        eventcount = 0
        links = self.soup.find_all("a", {"title" : lambda t: t and re.match(r'[0-9]+$',t)})
        for link in links:
            desc = link.parent.get_text().strip()
            rxres = re.match(RX_ANNIVERSARIES,desc,re.UNICODE)
            if not rxres:
                continue
            groups = rxres.groups()
            # Get BG image
            if get_images:
                image = None
                next_anchor_aslist = link.parent.select('a:nth-of-type(2)')
                next_anchor = next_anchor_aslist[0] if next_anchor_aslist else None
                if next_anchor:
                    ext_href = next_anchor.get('href', None)
                    if ext_href and ext_href.startswith('/wiki/'):
                        image = self.getLeadImageFromPage(ext_href[6:])
                        if image:
                            events.append({
                                'startyear': groups[0],
                                'description': groups[2],
                                'bg': image
                            })
            else:
                events.append({
                    'startyear': groups[0],
                    'description': groups[2],
                })
                
            eventcount += 1
            if maxevents and eventcount == maxevents: break

        return events

class EventExtractor1(EventExtractor):
    """
    Format 1: See 'List of Catholic Saints'
    """
    def extract(self, append_to=list()):
        events = append_to
        links = self.soup.find_all('span', {'class' : 'mw-headline'})
        for link in links:
            maybe_year = link.get_text().strip()
            if not re.match(r'[0-9]+$', maybe_year):
                continue
            year = maybe_year
            # Check for multiple events
            events_mkp = link.parent.find_next('ul').find_all('li')
            for e in events_mkp:
                media_url = None
                image = None
                first_anchor = e.a
                if first_anchor:
                    ext_href = first_anchor.get('href', None)
                    if ext_href and ext_href.startswith('/wiki/'):
                        media_url = URL_PREFIX_EN + ext_href
                        image = self.getLeadImageFromPage(ext_href[6:])
                desc = e.get_text().strip()
                events.append({
                    'startyear': year,
                    'description': desc,
                    'media_url': media_url,
                    'bg': image
                })
        return events

class EventExtractor2(EventExtractor):
    """
    Format 2: See 'Timeline of Canadian History,' 'History of same-sex marriage'
    """
    def extract(self, append_to=list()):
        events = append_to
        first_rows = self.soup.select('table.wikitable > tr:nth-of-type(1)')
        for row in first_rows:
            headers = row.find_all('th')
            year_hdr = row.find('th', text=re.compile('^(\s+)?[Y|y]ear'))
            date_hdr = row.find('th', text=re.compile('^(\s+)?[D|d]ate'))
            desc_hdr = row.find('th', text=re.compile('^(\s+)?[E|e]vent'))
            if not year_hdr:
                # If we can't get a year, move on... for now...
                continue
            year_col = headers.index(year_hdr)
            date_col = headers.index(date_hdr)
            desc_col = headers.index(desc_hdr)
            
            elem = row.find_next('tr') # this may mean moving from thead to tbody
            yearspan = 0 # Used to track years spanning multiple rows
            while elem and (not elem.name or elem.name == 'tr'):
                if elem.name == 'tr':
                    cells = elem.find_all('td')
                    if yearspan > 1:
                        colshift = 1 if year_col < date_col and year_col < desc_col else 0
                        # Above is always true in the case of the Canada example, but just in case
                        yearspan -= 1
                    else:
                        colshift = 0
                        raw_year = self.stripRefs(cells[year_col].get_text())
                        yearspan = int(cells[year_col].attrs['rowspan']) if 'rowspan' in cells[year_col].attrs else 0
                    startyr, endyr = self.getYearRange(raw_year)
                    # TODO:Need to revisit for dates
                    raw_date = self.stripRefs(cells[date_col-colshift].get_text())
                
                    # Attempt to get media URL, image
                    desc_cell = cells[desc_col-colshift]
                    media_url = None
                    image = None
                    first_anchor = desc_cell.a
                    if first_anchor:
                        ext_href = first_anchor.get('href', None)
                        if ext_href and ext_href.startswith('/wiki/'):
                            media_url = URL_PREFIX_EN + ext_href
                            image = self.getLeadImageFromPage(ext_href[6:])
                    raw_desc = self.stripRefs(desc_cell.get_text())
                    events.append({
                        'startyear': startyr,
                        'endyear': endyr,
                        'description': raw_desc,
                        'media_url': media_url,
                        'bg': image
                    })
                elem = elem.nextSibling

        return events

"""
Query: Base query object
"""
class Query(object):

    feedback = dict()

    """
    constructor -- get raw query text and set extractors
    """
    def __init__(self, raw):
        self.raw_query = raw
        self.extractors = [EventExtractorAnniv, EventExtractor1, EventExtractor2]

    """
    validate -- attempt to validate query text (may be a link or simple text), set error feedback if needed
    """
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
                    self.query = unquote(wiki_url_scan.groups()[0])
                    if get_markup: self.markup = buffer.getvalue()
                    return
            except:
                pass
            self.feedback['error'] = 'Link is not a valid Wikipedia link!'
        else:
            result = wikipedia.search(self.raw_query, suggestion=True)
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

    def get_events(self):
        soup = BeautifulSoup(self.markup, 'html.parser')
        self.events = []

        # Iterate through extractors (each corresponds to a different page format)
        i = 0
        while i < len(self.extractors) and not self.events:
            extractor_class = self.extractors[i]
            extractor = extractor_class(soup)
            self.events = extractor.extract(append_to=self.events)
            print self.events
            i += 1

        return self.events

"""
ThisDayQuery: query object for the 'This Day in History' loading module
"""
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
        self.extractors = [EventExtractorAnniv]

    def get_events(self):
        soup = BeautifulSoup(self.markup, 'html.parser')
        self.events = []

        # Iterate through extractor(s)
        i = 0
        while i < len(self.extractors) and not self.events:
            extractor_class = self.extractors[i]
            extractor = extractor_class(soup)
            self.events = extractor.extract(append_to=self.events,maxevents=5,get_images=False)
            i += 1

        return self.events
