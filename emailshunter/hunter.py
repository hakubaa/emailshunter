from concurrent import futures
import urllib.parse as urlparse
from collections import namedtuple
import requests

from requests.exceptions import RequestException

from emailshunter.webpage import find_urls, find_emails, WebPage, WebGraph
from emailshunter.util import url_fix, fmap


SearchResult = namedtuple("SearchResult", "page urls emails")


def update_netloc(root_url, url):
    '''Convert relative hyperlinks to absolute hyperlinks.'''
    root_scheme, root_netloc, *_ = urlparse.urlsplit(root_url)
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(url_fix(url))
    if not netloc:
        url = urlparse.urlunsplit((
            root_scheme, root_netloc, path, qs, anchor
        ))
    return url


def search_webpage(page, force_reload=False, head_first=True):
    '''Search webpage for emails and urls. Returns dict with found items.'''
    if not page.loaded or force_reload:
        page.reload()

    urls = [update_netloc(page.url, url) for url in find_urls(page)]
    emails = find_emails(page)
    return SearchResult(page=page, urls=urls, emails=emails)


class SearchManager:

    def __init__(self, max_workers=None, webgraph=None):
        self.webgraph = webgraph or WebGraph()
        self.emails = set()
        self.visited = set()
        self.max_workers = max_workers
        self.external_filters = []

    def add_filter(self, filter):
        self.external_filters.append(filter)

    def _filter_within_domain(self, root_url):
        def _filter(page):
            _, root_netloc, *_ = urlparse.urlsplit(root_url)
            _, netloc, *_ = urlparse.urlsplit(page.url)
            if root_netloc == netloc:
                return True
            else:
                return False
        return _filter

    def _search_wrapper(self, page):
        '''Search webpage and updage webgraph.'''
        # Verify content-type
        if not page.loaded:
            page.reload(head_request=True)
              
        content_type = page.headers.get("Content-Type", None)
        if not (content_type and content_type.startswith("text")):
            return SearchResult(page=page, urls=list(), emails=list())

        result = search_webpage(page)

        # Update webgraph
        for url in result.urls:
            self.webgraph.add_page(url, parent=page)

        # Update datasets
        self.emails |= set(result.emails)
        self.visited.add(page)

        return result

    def search(self, root_page, max_depth, within_domain=True):
        # Set filters
        filters = self.external_filters
        if within_domain:
            filters.append(self._filter_within_domain(root_page.url))

        # Submit hunter for root_page
        hunters = dict()

        with futures.ThreadPoolExecutor(self.max_workers) as executor:
            
            hunters[root_page] = executor.submit(self._search_wrapper, root_page)

            try:
                while hunters:

                    # Collect results
                    results = []
                    hunters2del = []
                    for key in hunters:
                        hunter = hunters[key]
                        if hunter.done():
                            print("Hunter '%s' done (%d hunters still loose)." % 
                                  (hunter, len(hunters)))
                            hunters2del.append(key)

                    for key in hunters2del:
                        del hunters[key]

                    # Check for new pages to visist
                    pages2visit = self.webgraph.find_nearest_neighbours(
                        root_page, max_depth, with_dist=False
                    )

                    if pages2visit:
                        # Apply filters
                        pages2visit = set(pages2visit) - self.visited
                        pages2visit = (page for page in pages2visit 
                                           if all(fmap(page, *filters)))
                        for page in pages2visit:
                            hunters[page] = executor.submit(self._search_wrapper, page)

            except KeyboardInterrupt:
                import pdb; pdb.set_trace(  )

        return 1