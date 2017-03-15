import unittest

from flask import current_app, url_for

from emailshunter import util

from .website.app import create_app
from .website import WebsiteTestCase


class WebsiteTest(WebsiteTestCase):

    def test_app_exists(self):
        self.assertFalse(current_app is None)
        
    def test_get_test_page(self):
        response = self.client.get("/test")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Test Page", content)


class UtilWithWebsiteTest(WebsiteTestCase):

    def test_get_resource_returns_webpage(self):
        content = util.get_resource("http://localhost:5000/test")
        self.assertIn("Test Page", content.decode("utf-8"))