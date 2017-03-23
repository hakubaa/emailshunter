import itertools

import requests
from bs4 import BeautifulSoup

import emailshunter.util as util


class WebPage:
    '''Representation of webpage.'''

    def __init__(self, url, load_page=True, params=None, **kwargs):
        self._url = util.normalize_url(url)
        if load_page:
            self.reload(params=params, **kwargs)

    def __hash__(self):
        return hash(self._url)

    def __eq__(self, other):
        return self._url == other._url

    @property
    def url(self):
        return self._url

    def reload(self, params=None, **kwargs):
        '''Reload webpage and updates links & emails.'''
        self._response = requests.get(self._url, params=params, **kwargs)

    def __getattr__(self, attr):
        '''Redirects attributes getter to response.'''
        if hasattr(self, "_response") and hasattr(self._response, attr):
                return getattr(self._response, attr)
        raise AttributeError("'%r' object has no attribute '%s', "
                             "try to reload the page." % (self, attr))


class WebGraph:
    '''Representation of relation between webpages.'''
    
    def __init__(self):
        self.graph = dict()
        self.pages = set()

    def add_relation(self, p1, p2):
        '''
        Add relation between pages to graph. Force using keyword parameters 
        to avoid mistakes.
        '''
        self.graph.setdefault(p1, set()).add(p2)
        self.graph.setdefault(p2, set()).add(p1)
        self.pages.add(p1)
        self.pages.add(p2)


def find_urls(page, normalize=True):
    '''Extracts all the URLs found within a page.'''
    soup = BeautifulSoup(page.content, "html.parser")
    urls = list(set(itertools.chain(
        util.find_with_re(str(soup), util.RE_URL),
        filter(
            lambda item: item and not item.startswith("mailto:"), 
            util.find_with_bs(soup, "a", "href")
        ))))
    if normalize:
        urls = [util.normalize_url(url) for url in urls]
    return urls


def find_emails(page):
    '''Extracts all the emails found within a page.'''
    soup = BeautifulSoup(page.content, "html.parser")
    emails = list(set(util.find_with_re(str(soup), util.RE_EMAIL)))
    return emails
