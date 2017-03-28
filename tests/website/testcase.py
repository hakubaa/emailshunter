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

    def mock_get_resource(self, mock):
        def get_resource(url, head_request=False):
            if head_request:
                response = self.client.head(url)
            else:
                response = self.client.get(url)
            if response.status_code != 200:
                raise Exception("HTTP ERROR")
            response.content = response.data
            return response
        mock.side_effect = get_resource        
        return mock

    def mock_requests_get(self, mock):
        def requests_get(*args, **kwargs):
            response = self.client.get(*args)
            response.content = response.data
            return response
        mock.side_effect = requests_get
        return mock