import unittest

from .app import create_app


class WebsiteTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies = True)

    def tearDown(self):
        self.app_context.pop()