#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models
import json, pycurl, re, requests, datetime, HTMLParser, wikipedia
from StringIO import StringIO
from bs4 import BeautifulSoup
from urllib import quote, unquote
from random import randint

# Source for below: http://daringfireball.net/2010/07/improved_regex_for_matching_urls
RX_URLMATCH = r'(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))'
URL_PREFIX_EN = 'https://en.wikipedia.org'
RX_WIKIURL = r'wikipedia\.org/wiki/(.+)'
RX_DATES = ur'\=\=\= ([0-9]+) \=\=\=[\r\n](\<\!\-\-.*\-\-\>[\r\n])?(?:(\* .+[\r\n])?)+'
ANNIVERSARIES = 'Wikipedia:selected anniversaries'
RX_ANNIVERSARIES = ur'([0-9]+) (–|-) (.*)'
RX_HYPHEN_SPLIT = ur'(.+) (–|-) (.+)$'

"""
EventExtractor - base extractor object declaration, format-specific extractors inherit from this
"""
class EventExtractor(object):
    def __init__(self, soup=None):
        self.soup = soup

    def strip_refs(self,txt):
        txt = txt.strip()
        RX = '\[[0-9]+\]'
        return re.sub(RX,'',txt)

    def get_next_sib(self, element):
        next = element.next_sibling
        while next == '\n':
            next = next.next_sibling
        return next

    def get_lead_image(self,page_id):
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

    def get_year_range(self,raw_txt):
        # print "Getting year range from: " + raw_txt
        # Check for BCE dates
        range_split = re.search(ur'((AD\s)?[0-9,]+(\sBC(E)?)?)?\s?([Bb]efore|[Uu]until|[Pp]rior to|to|–|-)?\s?([0-9,]+(\sBC(E)?)?)?',raw_txt,re.UNICODE)
        # Produces something like: (None, None, None, 'to', '14,000 BCE', ' BCE', 'E')
        if range_split:
            groups = range_split.groups()
            raw_start = groups[0]
            raw_end = groups[5]
            rx_digits = r'[^0-9]'
            if groups[4]:
                # We have a range
                endyr = re.sub(rx_digits,'',raw_end) if raw_end else datetime.datetime.now().strftime('%Y')
                # Kind of a hacky solution here to prevent scale distortion
                startyr = re.sub(rx_digits,'',raw_start) if raw_start else endyr
                if groups[6]:
                    # Both start and end must be negative...
                    print '-'+startyr, '-'+endyr
                    return '-'+startyr, '-'+endyr
                elif groups[2]:
                    print '-'+startyr, endyr
                    return '-'+startyr, endyr
            else:
                startyr = re.sub(rx_digits,'',raw_start)
                endyr = startyr
                if groups[2]:
                    print '-'+startyr, '-'+endyr
                    return '-'+startyr, '-'+endyr
            print startyr, endyr
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
                        image = self.get_lead_image(ext_href[6:])
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
        sections = self.soup.find_all('span', {'class' : 'mw-headline'})
        for hdr in sections:
            maybe_year = hdr.get_text().strip()
            if not re.match(r'[0-9]+$', maybe_year):
                continue
            year = maybe_year
            l = self.get_next_sib(hdr.parent)
            if not l or not l.name in ['ul','ol']:
                continue
            # Check for multiple events
            events_mkp = l.find_all('li')
            for e in events_mkp:
                media_url = None
                image = None
                first_anchor = e.a
                if first_anchor:
                    ext_href = first_anchor.get('href', None)
                    if ext_href and ext_href.startswith('/wiki/'):
                        media_url = URL_PREFIX_EN + ext_href
                        image = self.get_lead_image(ext_href[6:])
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
                        raw_year = self.strip_refs(cells[year_col].get_text())
                        yearspan = int(cells[year_col].attrs['rowspan']) if 'rowspan' in cells[year_col].attrs else 0
                    startyr, endyr = self.get_year_range(raw_year)
                    # TODO:Need to revisit for dates
                    raw_date = self.strip_refs(cells[date_col-colshift].get_text())
                
                    # Attempt to get media URL, image
                    desc_cell = cells[desc_col-colshift]
                    media_url = None
                    image = None
                    first_anchor = desc_cell.a
                    if first_anchor:
                        ext_href = first_anchor.get('href', None)
                        if ext_href and ext_href.startswith('/wiki/'):
                            media_url = URL_PREFIX_EN + ext_href
                            image = self.get_lead_image(ext_href[6:])
                    raw_desc = self.strip_refs(desc_cell.get_text())
                    events.append({
                        'startyear': startyr,
                        'endyear': endyr,
                        'description': raw_desc,
                        'media_url': media_url,
                        'bg': image
                    })
                elem = elem.nextSibling

        return events

class EventExtractor3(EventExtractor):
    """
    Format 3: See 'Timeline of Communication Technology'
    """

    def _get_last_link(self, soup_obj, raw_desc):
        links = soup_obj.find_all('a')
        RX = r'\[[0-9]+\]$'
        if re.search(RX,raw_desc):
            if len(links) > 1:
                link_index = -2
            else:
                link_index = None
        else:
            link_index = -1
        result = links[link_index].get('href', None) if (links and link_index) else None
        return result

    def extract(self, append_to=list()):
        events = append_to
        sections = self.soup.find_all('span', {'class' : 'mw-headline'})

        # Basically the below are used to infer if this page is in fact a timeline,
        # depending on how many list items are recognized as beginning with dates
        years_recognized, items_checked = 0, 0

        for hdr in sections:
            l = self.get_next_sib(hdr.parent)
            if not l or not l.name in ['ul','ol']:
                continue

            listitems = l.find_all('li')

            for li in listitems:
                probable_events = []
                subitems = li.find_all('li')
                if len(subitems) > 0:
                    # Handle nested lists
                    raw_dates = li.next if li.next and not li.next.name else None
                    if raw_dates:
                        raw_dates = raw_dates.strip()
                        startyr, endyr = self.get_year_range(raw_dates)
                        for item in subitems:
                            raw_desc = item.get_text()
                            desc = self.strip_refs(raw_desc)
                            media_url = self._get_last_link(item, raw_desc)
                            probable_events.append((startyr,endyr,raw_desc,media_url))
                else:
                    rx = re.match(RX_HYPHEN_SPLIT, li.get_text(), re.UNICODE)
                    if rx:
                        raw_dates = rx.groups()[0].strip()
                        startyr, endyr = self.get_year_range(raw_dates)
                        raw_desc = rx.groups()[2]
                        desc = self.strip_refs(raw_desc)
                        media_url = self._get_last_link(li, raw_desc)
                        probable_events.append((startyr,endyr,desc,media_url))

                for pe in probable_events:
                    event = dict()
                    if pe[0]: event['startyear'] = pe[0]
                    if pe[1]: event['endyear'] = pe[1]
                    event['description'] = pe[2]
                    if pe[3]:
                        event['media_url'] = URL_PREFIX_EN + pe[3]
                        if pe[3].startswith('/wiki/'):
                            image = self.get_lead_image(pe[3][6:])
                            if image:
                                event['bg'] = image
                    events.append(event)
            
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
        self.extractors = [EventExtractorAnniv, EventExtractor1, EventExtractor2, EventExtractor3]

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
            self.feedback['error'] = 'Sorry, this link is not a valid Wikipedia link.'
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
                self.feedback['lead'] = "Sorry, I couldn't find anything."
                self.feedback['clarification'] = "Did you mean to search for one of the items below?"
                self.feedback['suggestions'] = result[0]
            else:
                # We got nothing...
                print "No matching page found, and no suggestions are available."
                self.feedback['lead'] = "Sorry, I couldn't find anything."
                self.feedback['error'] = "Please check the spelling of the query."\
                                         "It might be easier to copy the link of the page you want to turn into a Timeline."

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

    """
    get_events - iterate through extractors until one is found (or not) that matches the page format, and extract events
    """
    def get_events(self):
        soup = BeautifulSoup(self.markup, 'html.parser')
        self.events = []

        # Iterate through extractors (each corresponds to a different page format)
        i = 0
        num_events = 0
        while i < len(self.extractors) and not self.events:
            extractor_class = self.extractors[i]
            extractor = extractor_class(soup)
            self.events = extractor.extract(append_to=self.events)
            
            print "Extracted %d events using %s" % (len(self.events)-num_events, type(extractor).__name__)
            num_events += len(self.events)
            i += 1

        self._get_headlines()

        return self.events

    """
    _get_headlines - Assign raw descriptions to be either headlines or descriptions based on length
    """
    def _get_headlines(self):
        if hasattr(self, 'events'):
            for e in self.events:
                if len(e['description']) < 100 or 'bg' not in e:
                    e['headline'] = e['description']
                    e['description'] = ''

    """
    get_title_img - attempt to retrieve the main image from the queried page, return None on fail
    """
    def get_title_image(self):
        e = EventExtractor()
        page_url = quote(self.query)
        image = e.get_lead_image(page_url)
        # If we can't find an image in the title page, we randomly select one from the events
        if hasattr(self, 'events') and self.events:
            while not image:
                random_event = self.events[randint(0,len(self.events)-1)]
                image = random_event['bg'] if 'bg' in random_event else None
        return image

    """
    titlefy - make into title for presentation to user
    """
    def titlefy(self):
        if hasattr(self, 'query'):
            return self.query.title()
        else:
            return None

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

class Timeline(models.Model):
    title = models.CharField(max_length=256)
    json = models.CharField(max_length=1000000)