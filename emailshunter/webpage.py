import itertools
from queue import PriorityQueue

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
        self.pages = dict()

    def add_relation(self, p1, p2):
        '''
        Add relation between pages to graph. Force using keyword parameters 
        to avoid mistakes.
        '''
        self.graph.setdefault(p1, set()).add(p2)
        self.graph.setdefault(p2, set()).add(p1)
        if not p1 in self.pages: self.pages[p1] = p1
        if not p2 in self.pages: self.pages[p2] = p2

    def find_path(self, pstart, pend):
        '''
        Looks for the shorthest path between two pages. Returns tuple containing
        consequtive pages in the path or None if there is not path.
        '''

        # Ensure pstart and pend are WebPage-s.
        if not isinstance(pstart, WebPage):
            pstart = self._url2webpage(pstart)
        if not isinstance(pend, WebPage):
            pend = self._url2webpage(pend)

        # Return None when one of the pages does not exist in the graph.
        if not pstart in self or not pend in self:
            return None

        # Return None when one of the pages has no connections
        if not pstart in self.graph or not pend in self.graph:
            return None

        # Test whether the pages are directly connected
        if pend in self.graph[pstart] or pstart in self.graph[pend]:
            return (pstart, pend)

        # Implementation of Dijkstra's algorithm
        not_visited = set(self.pages)
        dists = { page: len(self)+1 for page in not_visited }
        dists[pstart] = 0
        prevs = { page: None for page in not_visited }

        while not_visited:
            min_dist = min(dists[item] for item in dists if item in not_visited)
            current = next(p for p in not_visited if dists[p] == min_dist)
            not_visited -= set((current,))
        
            # Shortes path has been found            
            if current == pend:
                break

            current_dist = dists[current]
            for page in self.graph[current]:
                alt = current_dist + 1
                if alt < dists[page]:
                    dists[page] = alt
                    prevs[page] = current

        path = list()
        target = pend
        while prevs[target]:
            path.append(target)
            target = prevs[target]
        else:
            if path: path.append(target)

        return tuple(reversed(path)) or None


    def get_page(self, url, create_new=True):
        '''
        Returns page with given url or creates new one if there is no page 
        with the url.
        '''
        url = util.normalize_url(url)
        return self.pages.get(
            WebPage(url, load_page=False), 
            (create_new and WebPage(url=url, load_page=False) or None)
        )

    def add_page(self, obj, parent=None):
        '''
        Adds page to graph. Accepts WebPage or url(string).
        '''
        if not isinstance(obj, WebPage):
            obj = self._url2webpage(obj)
        self.pages[obj] = obj
        if parent:
            self.add_relation(obj, parent)
        return obj

    def _url2webpage(self, url):
        return WebPage(url=util.normalize_url(url), load_page=False)

    def __contains__(self, page):
        if not isinstance(page, WebPage):
            page = self._url2webpage(page)
        return page in self.pages

    def __getitem__(self, page):
        if not isinstance(page, WebPage):
            page = self._url2webpage(page)
        return self.pages[page]

    def __len__(self):
        return len(self.pages)


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
