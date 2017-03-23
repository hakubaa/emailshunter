import re
import urllib.parse as urlparse
import imp
import importlib
import sys
import inspect
import ctypes

import requests
from bs4 import BeautifulSoup


RE_EMAIL = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
RE_URL = r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"


def get_resource(uri, timeout=None, head_request=False):
    '''Return resource from given uri.'''
    if head_request:
        resp = requests.head(uri, timeout=timeout)
    else:
        resp = requests.get(uri, timeout=timeout)
    if resp.status_code != 200:
        resp.raise_for_status()
    return resp


def find_with_re(text, pattern):
    '''Return an iterator over all non-overlapping matches in the text.'''
    rpattern = re.compile(pattern)
    return (match.group() for match in rpattern.finditer(text))


def find_with_bs(soup, tag, attr=None):
    '''
    Return an iterator over all non-overlapping tags/attr in the page. When attr
    is not null return the value of the attr, otherwise the value of the tag.
    '''
    tags = soup.find_all(tag)
    return ((not attr and tag) or tag.get(attr, None) for tag in tags)


def filter_with_re(iterable, pattern=None):
    if not pattern:
        return iterable
    rpattern = re.compile(pattern)
    return (item for item in iterable if rpattern.match(item))


def url_fix(s, charset='utf-8'):
    """Fix url."""
    if isinstance(s, bytes):
        s = s.decode(charset, 'ignore')
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urlparse.quote(path, '/%')
    qs = urlparse.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))


def normalize_url(url, charset="utf-8"):
    '''Normalize url. Get rid of query and anchor.'''
    if isinstance(url, bytes):
        url = url.decode(charset, errors="ignore")
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(url)
    path = urlparse.quote(path, "/%")
    if path == "": path = "/"
    return urlparse.urlunsplit((scheme, netloc, path, qs, None))


def load_module(name, attach = False, force_reload = True):
    '''Load dynamically module.'''
    if name in sys.modules and force_reload:
        module = imp.reload(sys.modules[name])
    else:
        module = importlib.import_module(name)
    if attach:
        calling_frame = inspect.stack()[1][0]
        calling_frame.f_locals.update(
            { attr: getattr(module, attr) for attr in dir(module) 
                                          if not attr.startswith("_") }
        )
        ctypes.pythonapi.PyFrame_LocalsToFast(
                ctypes.py_object(calling_frame), ctypes.c_int(0))
    return module


def fmap(item, *args):
    '''Applies each func in args to item, yielding the result.'''
    return (f(item) for f in args)