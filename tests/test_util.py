import unittest
from unittest.mock import patch, Mock

from emailshunter import util


@patch("emailshunter.util.requests.get") 
class GetResourceTest(unittest.TestCase):

    def test_for_calling_request_method_with_correct_uri(self, get_mock):
        resource = util.get_resource(uri="http://localhost")
        args = get_mock.call_args[0] # positional arguments
        self.assertEqual(args[0], "http://localhost")

    def test_for_calling_raise_for_status_when_not_200(self, get_mock):
        get_mock.return_value.status_code = 404
        resource = util.get_resource("http://localhost")
        self.assertTrue(get_mock.return_value.raise_for_status.called)

    def test_for_returning_content_of_response(self, get_mock):
        resp = Mock()
        resp.status_code = 200
        resp.content = b"<html></html>"
        get_mock.return_value = resp
        resource = util.get_resource("fake_uri")
        self.assertEqual(resource, resp.content)


class FindWithReTest(unittest.TestCase):

    def test_for_finding_email_addresses(self):
        content = "BlaBla test@test.com amazing 'admin@test.com'"
        emails = list(util.find_with_re(content, util.RE_EMAIL))
        self.assertEqual(len(emails), 2)
        self.assertEqual(emails[0], "test@test.com")
        self.assertEqual(emails[1], "admin@test.com")

    def test_for_finding_urls(self):
        content = """"
        This page 'http://www.awesome.com' is awesome. But this one
        https://www.notawesome.pl is not.
         """
        urls = list(util.find_with_re(content, util.RE_URL))
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "http://www.awesome.com")

    def test_for_finding_urls_with_bs(self):
        content = """
        <html><head><title>Test Page</title></head>
        <body>
            <h1>My Favourite Web Pages</h1>
            <ul>
                <li><a href="http://www.google.com">Google</a></li>
                <li><a>No Href</a></li>
                <li><a href="www.sport.com">Sport</a></li>
            </ul>
        </body>

        """
        urls = list(util.find_with_bs(content, tag="a", attr="href"))
        self.assertEqual(len(urls), 3)
        self.assertCountEqual(["http://www.google.com", None, "www.sport.com"],
                              urls)


class FilterWithReTest(unittest.TestCase):

    def test_returns_iterable_with_matching_elements(self):
        test_iter = [ "test.com", "http://test.com", "www.invalid.org" ]
        result = list(util.filter_with_re(test_iter, r".*test.*"))
        self.assertEqual(len(result), 2)
        self.assertCountEqual(test_iter[:2], result)

    def test_returns_empty_iterable_if_no_item_match_pattern(self):
        test_iter = [ "abc", "def", "ghg" ]
        result = list(util.filter_with_re(test_iter, r"^test.*"))
        self.assertFalse(result)