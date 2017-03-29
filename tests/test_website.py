import unittest

from flask import current_app, url_for

from crawlengine import util

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