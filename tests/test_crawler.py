from unittest.mock import patch

from .website import WebsiteTestCase

from crawlengine.crawler import search_webpage, SearchManager
from crawlengine.webpage import WebPage


def patch_requests_get(pass_mock=False):
    def _wrapper(func):
        def _test_method(self, res_mock):
            self.mock_requests_get(res_mock)
            if pass_mock:
                return func(self, res_mock)
            else:
                return func(self)
        return _test_method
    return _wrapper


@patch("requests.get")
class SearchWebpageTest(WebsiteTestCase):        

    @patch_requests_get()
    def test_for_finding_emails(self):
        page = WebPage("http://localhost:5000/test")
        result = search_webpage(page)
        self.assertEqual(len(result.emails), 1)
        self.assertIn("wait@for.it", result.emails)

    @patch_requests_get()
    def test_for_finding_sites(self):
        page = WebPage("http://localhost:5000/test")
        result = search_webpage(page)
        self.assertEqual(len(result.urls), 1)
        self.assertIn("http://localhost:5000/test", list(result.urls))


@patch("requests.get")
class SearchManagerTest(WebsiteTestCase):

    @patch_requests_get()
    def test_max_depth_limits_depth_of_traversed_web_pages(self):
        page = WebPage("http://localhost:5000")
        sm = SearchManager(max_workers=5)
        sm.search(page, max_depth=1)
        self.assertEqual(len(sm.visited), 11)

    @patch_requests_get()
    def test_updates_graph_of_web_site(self):
        page = WebPage("http://localhost:5000")
        sm = SearchManager(max_workers=5)
        sm.search(page, max_depth=100)
        self.assertEqual(len(sm.webgraph.graph[page]), 10)