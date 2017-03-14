import re

import requests
from bs4 import BeautifulSoup


RE_EMAIL = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
RE_URL = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")


def get_resource(uri, timeout=None):
    '''Return resource from given uri.'''
    resp = requests.get(uri, timeout=timeout)
    if resp.status_code != 200:
        resp.raise_for_status()
    return resp.content


def find_with_re(text, rpattern):
    '''Return an iterator over all non-overlapping matches in the text.'''
    return (match.group() for match in rpattern.finditer(text))


def find_with_bs(text, tag, attr=None):
    '''
    Return an iterator over all non-overlapping tags/attr in the page. When attr
    is not null return the value of the attr, otherwise the value of the tag.
    '''
    soup = BeautifulSoup(text, "html.parser")
    tags = soup.find_all(tag)
    return ((not attr and tag) or tag.get(attr, None) for tag in tags)