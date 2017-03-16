from unittest.mock import patch

from .website import WebsiteTestCase

from emailshunter.hunter import Hunter


@patch("emailshunter.hunter.get_resource")
class HunterTest(WebsiteTestCase):        

    def mock_get_resource(self, mock):
        def get_resource(url):
            response = self.client.get(url)
            if response.status_code != 200:
                raise Exception("HTTP ERROR")
            return response.data
        mock.side_effect = get_resource        
        return mock

    def test_for_finding_emails(self, res_mock):
        self.mock_get_resource(res_mock)
        hunter = Hunter("http://localhost:5000/test")
        result = hunter.find()
        self.assertEqual(len(result.emails), 1)
        self.assertIn("wait@for.it", result.emails)

    def test_for_finding_sites(self, res_mock):
        self.mock_get_resource(res_mock)
        hunter = Hunter("http://localhost:5000/test")
        result = hunter.find()
        self.assertEqual(len(result.urls), 1)
        self.assertIn("http://localhost:5000/test", list(result.urls))

    def test_raises_error_when_invalid_url(self, res_mock):
        self.mock_get_resource(res_mock)
        hunter = Hunter("http://localhost:5000/dfsfdsdf")
        with self.assertRaises(Exception):
            hunter.find()