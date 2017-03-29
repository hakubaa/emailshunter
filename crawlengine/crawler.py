from concurrent import futures
import urllib.parse as urlparse
from collections import namedtuple
import requests

from requests.exceptions import RequestException

from crawlengine.webpage import find_urls, find_emails, WebPage, WebGraph
from crawlengine.util import url_fix, fmap


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


def search_webpage(page):
    '''Search webpage for emails and urls. Returns dict with found items.'''
    if not page.loaded:
        raise ValueError("empty WebPage object, reload required")

    content_type = page.headers.get("Content-Type", None)
    if not (content_type and content_type.startswith("text")):
        return SearchResult(page=page, urls=list(), emails=list())

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

    def _update_internals(self, page):
        '''Search webpage and updage webgraph.'''
        result = search_webpage(page)

        # Update webgraph
        for url in result.urls:
            self.webgraph.add_page(url, parent=page)

        # Update datasets
        self.emails |= set(result.emails)
        self.visited.add(page)

    def search(self, root_page, max_depth, within_domain=True):

        print("\nPress CTRL+C to stop the script.\n")

        # Set filters
        filters = self.external_filters
        if within_domain:
            filters.append(self._filter_within_domain(root_page.url))

        pages_in_progress = dict()

        with futures.ThreadPoolExecutor(self.max_workers) as executor:
            # Submit crawler for root_page
            pages_in_progress[root_page] = executor.submit(root_page.reload)

            try:
                while pages_in_progress:
                    # Collect results
                    results = []
                    pages_done = []
                    for page in pages_in_progress:
                        future = pages_in_progress[page]
                        if future.done():
                            print("COMPLETE: {!r}.".format(page))
                            self._update_internals(page)
                            pages_done.append(page)

                    for page in pages_done:
                        del pages_in_progress[page]

                    # Check for new pages to visist
                    pages2visit = self.webgraph.find_nearest_neighbours(
                        root_page, max_depth, with_dist=False
                    )

                    if pages2visit:
                        # Apply filters
                        pages2visit = set(pages2visit) - self.visited - \
                                      set(pages_in_progress)
                        pages2visit = (page for page in pages2visit 
                                           if all(fmap(page, *filters)))
                        for page in pages2visit:
                            pages_in_progress[page] = executor.submit(page.reload)

            except KeyboardInterrupt:
                print("Waiting for running task to complete ...")
                # Stop executor and collect results
                executor.shutdown()
                for page in pages_in_progress:
                    future = pages_in_progress[page]
                    if future.done():
                        print("COMPLETE: {!r}.".format(page))
                        self._update_internals(page)


def avoid_extensions(exts=["bmp", "jpeg", "jpg", "pdf", "php", "css", "js", 
                           "ico", "png"]):
    def _filter(page):
        _, _, path, *_ = urlparse.urlsplit(page.url)
        return all(map(lambda ext: not path.endswith(ext), exts))
    return _filter


def avoid_urls_matching(pattern):
    def _filter(page):
        if not re.match(pattern, page.url):
            return True
        return False
    return _filter