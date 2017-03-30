from concurrent import futures
from collections import namedtuple
import urllib.parse as urlparse
import requests
import pdb
import csv
import operator
from functools import reduce

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

    def __init__(self, max_workers=1, webgraph=None, callback=None):
        self.webgraph = webgraph or WebGraph()
        self._emails = dict()
        self.max_workers = max_workers
        self.external_filters = []
        self.callback = callback

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
        for url in result.urls:
            self.webgraph.add_page(url, parent=page)
        self._emails.setdefault(page, set()).update(result.emails)

    @property
    def visited(self):
        return self._emails.keys()

    @property
    def emails(self):
        return reduce(operator.or_, self._emails.values(), set())

    def __getitem__(self, page):
        return self._emails[page]

    def _submit_worker(self, page, executor):
        future = executor.submit(page.reload)
        if self.callback:
            future.add_done_callback(self.callback)
        return future

    def search(self, root_page, max_depth, within_domain=True):

        # Set filters
        filters = self.external_filters
        if within_domain:
            filters.append(self._filter_within_domain(root_page.url))

        workers = dict()

        with futures.ThreadPoolExecutor(self.max_workers) as executor:
            workers[root_page] = self._submit_worker(root_page, executor)
            try:
                while workers:
                    # Collect pages
                    for page, future in list(workers.items()):
                        if future.done():
                            self._update_internals(page)
                            del workers[page]

                    # Check for new pages to visist
                    pages2visit = self.webgraph.find_nearest_neighbours(
                        root_page, max_depth, with_dist=False
                    )

                    if pages2visit:
                        # Apply filters
                        pages2visit = set(pages2visit) - self.visited - set(workers)
                        pages2visit = (page for page in pages2visit 
                                           if all(fmap(page, *filters)))
                        for page in pages2visit:
                            workers[page] = self._submit_worker(page, executor)

            except KeyboardInterrupt:
                executor.shutdown()
                for page, future in workers.items():
                    if future.done():
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


def save_to_csv(path, manager):
    '''Save emails & pages visited by crawler to csv file.'''
    with open(path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=";", quotechar="|", 
                            quoting=csv.QUOTE_MINIMAL)
        writer.writerow(("page", "email"))
        for page in manager.visited:
            for email in manager[page]:
                writer.writerow((page.url, email))