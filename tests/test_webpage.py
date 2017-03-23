import unittest
from unittest.mock import patch, Mock

from emailshunter.webpage import WebPage, WebGraph, find_urls, find_emails


def patch_requests_get(pass_mock=False):
    def _wrapper(func):
        def _test_method(self, res_mock):
            response = Mock()
            response.content = b"<html></html>"
            response.headers = {"Content-Type": "text/html"}
            res_mock.return_value = response
            if pass_mock:
                return func(self, res_mock)
            else:
                return func(self)
        return _test_method
    return _wrapper


@patch("emailshunter.webpage.requests.get")
class TestWebPage(unittest.TestCase):
    
    @patch_requests_get()
    def test_pages_with_the_same_url_have_similar_hash(self):
        p1 = WebPage("http://www.test.page.com")
        p2 = WebPage("http://www.test.page.com")
        self.assertEqual(hash(p1), hash(p2))

    @patch_requests_get()
    def test_pages_with_the_same_url_are_equal(self):
        p1 = WebPage("http://www.test.page.com")
        p2 = WebPage("http://www.test.page.com")
        self.assertEqual(p1, p2)

    @patch_requests_get()
    def test_raises_error_when_changing_url(self):
        p1 = WebPage("http://www.you.can.change.me")
        with self.assertRaises(AttributeError):
            p1.url = "http://www.I.can.do.everything"

    @patch_requests_get(True)
    def test_constructor_loads_page_by_default(self, get_mock):
        p1 = WebPage("http://localhost:5000/")
        get_mock.assert_called_once_with("http://localhost:5000/", params=None)

    @patch_requests_get(True)
    def test_for_turning_off_loading_page_in_constructor(self, get_mock):
        p1 = WebPage("http://localhost:5000", load_page=False)
        self.assertFalse(get_mock.called)

    @patch_requests_get(True)
    def test_reload_sets_content_and_headers_attribute(self, get_mock):
        page = WebPage("http://localhost:5000")
        self.assertEqual(page.content, b"<html></html>")
        self.assertEqual(page.headers, {"Content-Type": "text/html"})


@patch("emailshunter.webpage.requests.get")
class FindEmailsAndUrlsTest(unittest.TestCase):

    @patch_requests_get(True)
    def test_for_extracting_urls(self, get_mock):
        response = Mock()
        response.content = b"""
            <html>
            <body>
                <a href='test.html'>Test</a>
                <a href="mailto:test@gil.com">E-Mail</a>
                Contact: test@one.two
            </body>
            </html>
        """
        response.headers = {"Content-Type": "text/html"}
        get_mock.return_value = response
        page = WebPage("http://localhost:5000", load_page=False)
        page.reload()
        links = find_urls(page)
        self.assertTrue(len(links), 1)
        self.assertEqual(links[0], "test.html")

    @patch_requests_get(True)
    def test_for_extracting_emails(self, get_mock):
        response = Mock()
        response.content = b"""
            <html>
            <body>
                <a href='test.html'>Test</a>
                <a href="mailto:test@gil.com">E-Mail</a>
                Contact: test@one.two
            </body>
            </html>
        """
        response.headers = {"Content-Type": "text/html"}
        get_mock.return_value = response
        page = WebPage("http://localhost:5000", load_page=False)
        page.reload()
        emails = find_emails(page)
        self.assertTrue(len(emails), 2)
        self.assertCountEqual(emails, ["test@gil.com", "test@one.two"])


class WebGraphTest(unittest.TestCase):
     
    def test_for_adding_relation_between_pages(self):
        p1 = WebPage("test1", load_page=False)
        p2 = WebPage("test2", load_page=False)
        wg = WebGraph()
        wg.add_relation(p1, p2)
        self.assertIn(p2, wg.graph[p1])
        self.assertIn(p1, wg.graph[p2])