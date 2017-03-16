from collections import namedtuple
from concurrent import futures
from queue import Queue
import itertools
import urllib.parse as urlparse

from requests.exceptions import RequestException

from emailshunter.util import *

HuntResult = namedtuple("HuntResult", "hunter urls emails")


class Hunter:

    def __init__(self, url, cache=True):
        self.url = url_fix(url)
        self.cache = True
        self.prey = None

    def update_netloc(self, iterable):
        '''Convert relative hyperlinks to absolute hyperlinks.'''
        root_scheme, root_netloc, *_ = urlparse.urlsplit(self.url)
        for url in iterable:
            scheme, netloc, path, qs, anchor = urlparse.urlsplit(url_fix(url))
            if not netloc:
                url = urlparse.urlunsplit((
                    root_scheme, root_netloc, path, qs, anchor
                ))
            yield url

    def find(self):
        '''Find all urls and emails in the wepage.'''
        if self.cache and self.prey:
            return self.prey
        try:
            res = get_resource(self.url).decode("utf-8")
        except RequestException as e:
            return HuntResult(hunter=self, urls=list(), emails=list())
        result = HuntResult(
            hunter=self,
            urls=list(self.update_netloc(find_with_re(res, RE_URL))) +
                 list(self.update_netloc(
                    filter(lambda item: item and not item.startswith("mailto:"), 
                    find_with_bs(res, "a", "href")))
                 ),
            emails = list(find_with_re(res, RE_EMAIL))
        )
        self.prey = result
        return result


class HuntManager:

    def __init__(self, root_url, filters=None, within_domain=True):
        self.root_url = root_url
        self.visited_urls = set()
        self.emails = set()
        self.filters = list(filters or [])
        self.add_filter(self._filter_not_visited)
        if within_domain:
            self.add_filter(self._filter_within_domain)

    def add_filter(self, filter):
        self.filters.append(filter)

    def _filter_not_visited(self, url):
        '''Verifies if url has not been yet visited.'''
        return url not in self.visited_urls

    def _filter_within_domain(self, url):
        _, root_netloc, *_ = urlparse.urlsplit(self.root_url)
        _, netloc, *_ = urlparse.urlsplit(url)
        if root_netloc == netloc:
            return True
        else:
            return False

    def run(self, concur_req=5):
        with futures.ThreadPoolExecutor(max_workers=concur_req) as executor:
            hunters = []
            
            # Create hunter to visit root_url
            future = executor.submit(Hunter(self.root_url).find)
            hunters.append(future)
            
            urls2visit = set()

            while hunters or urls2visit:
                # Collect results
                results = []
                for hunter in list(hunters):
                    if hunter.done():
                        results.append(hunter.result())
                        del hunters[hunters.index(hunter)]

                # Aggregate results
                for result in results:
                    self.emails |= set(result.emails)
                    urls2visit |= set(url for url in result.urls 
                                          if all(fmap(url, *self.filters)))

                # Spawn new hunters
                for url in urls2visit:
                    print("Spawn a Hunter to: %s" % url)
                    hunters.append(executor.submit(Hunter(url).find))
                    self.visited_urls.add(url)

                urls2visit = set()


        return HuntResult(
            hunter=self, emails=list(self.emails), 
            urls=list(self.visited_urls)
        )