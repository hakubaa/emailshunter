from collections import namedtuple
from concurrent import futures
from queue import Queue
import itertools
import urllib.parse as urlparse
import re

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

        # Default result 
        result = HuntResult(hunter=self, urls=list(), emails=list())

        try:
            res = get_resource(self.url, head_request=True)
        except RequestException as e:
            pass # ignore exception - it's ok - return default value
        else:
            if res.headers.get("Content-Type", "").startswith("text"):
                try:
                    res = get_resource(self.url)
                except RequestException as e:
                    pass # ignore exception - it's ok - return default value
                else:
                    content = res.content
                    content = content.decode(
                        getattr(res, "encoding", "utf-8"), errors="ignore"
                    )
                    soup = BeautifulSoup(content, "html.parser")
                    result = HuntResult(
                        hunter=self,
                        urls=list(self.update_netloc(find_with_re(content, RE_URL))) +
                             list(self.update_netloc(filter(
                                lambda item: item and not item.startswith("mailto:"), 
                                find_with_bs(soup, "a", "href")
                             ))),
                        emails = list(find_with_re(content, RE_EMAIL))
                    )
        self.prey = result
        return result


class HuntManager:

    def __init__(self, root_url, filters=None, within_domain=True, 
                 max_depth=None):
        self.root_url = root_url
        self.visited_urls = set()
        self.emails = set()
        self.filters = list(filters or [])
        self.hunters = dict()
        self.max_depth = max_depth

        # Append built-in filters
        self.add_filter(self._filter_not_visited)
        if within_domain:
            self.add_filter(self._filter_within_domain)

    def add_filter(self, filter):
        self.filters.append(filter)

    def _filter_not_visited(self, url):
        '''Verifies if url has not been yet visited.'''
        url = normalize_url(url)
        return url not in self.visited_urls and url not in self.hunters.values()

    def _filter_within_domain(self, url):
        _, root_netloc, *_ = urlparse.urlsplit(self.root_url)
        _, netloc, *_ = urlparse.urlsplit(url)
        if root_netloc == netloc:
            return True
        else:
            return False

    def _add_hunter(self, url, executor, depth):
        future = executor.submit(Hunter(url).find)
        self.hunters[future] = (normalize_url(url), depth)
        return future

    def _add_to_visited(self, url):
        self.visited_urls.add(normalize_url(url))

    def run(self, concur_req=5):

        with futures.ThreadPoolExecutor(max_workers=concur_req) as executor:
            # Create hunter to visit root_url
            self._add_hunter(self.root_url, executor, 0) # 0 - init depth
            urls2visit = set()

            try:
                while self.hunters or urls2visit:
                    # Collect results
                    results = []
                    hunters2del = []
                    for hunter in self.hunters.keys():
                        if hunter.done():
                            print("Hunter '%s' done (%d hunters still loose)." % 
                                  (self.hunters[hunter][0], len(self.hunters)))
                            results.append(
                                (hunter.result(), self.hunters[hunter][1])
                            )
                            self._add_to_visited(self.hunters[hunter][0])
                            hunters2del.append(hunter)

                    for hunter in hunters2del:
                        del self.hunters[hunter]

                    # Aggregate results
                    for result, depth in results:
                        self.emails |= set(result.emails)
                        if self.max_depth and depth < self.max_depth:
                            urls2visit |= set(url for url in result.urls 
                                                  if all(fmap(url, *self.filters)))

                    # Spawn new hunters
                    for url in urls2visit:
                        self._add_hunter(url, executor)
                    urls2visit = set()

            except KeyboardInterrupt:
                import pdb; pdb.set_trace(  )


        return HuntResult(
            hunter=self, emails=list(self.emails), 
            urls=list(self.visited_urls)
        )


def avoid_extensions(exts=["bmp", "jpeg", "jpg", "pdf", "php", "cs", "js", 
                           "ico", "png"]):
    def _filter(url):
        _, _, path, *_ = urlparse.urlsplit(url)
        return all(map(lambda ext: not path.endswith(ext), exts))
    return _filter

def avoid_urls_matching(pattern):
    def _filter(url):
        if not re.match(pattern, url):
            return True
        return False
    return _filter