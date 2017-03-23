from unittest.mock import patch

from .website import WebsiteTestCase

from emailshunter.hunter import Hunter, HuntManager


def patch_get_resource(pass_mock=False):
    def _wrapper(func):
        def _test_method(self, res_mock):
            self.mock_get_resource(res_mock)
            if pass_mock:
                return func(self, res_mock)
            else:
                return func(self)
        return _test_method
    return _wrapper


@patch("emailshunter.hunter.get_resource")
class HunterTest(WebsiteTestCase):        

    @patch_get_resource()
    def test_for_finding_emails(self):
        hunter = Hunter("http://localhost:5000/test")
        result = hunter.find()
        self.assertEqual(len(result.emails), 1)
        self.assertIn("wait@for.it", result.emails)

    @patch_get_resource()
    def test_for_finding_sites(self):
        hunter = Hunter("http://localhost:5000/test")
        result = hunter.find()
        self.assertEqual(len(result.urls), 1)
        self.assertIn("http://localhost:5000/test", list(result.urls))

    @patch_get_resource()
    def test_raises_error_when_invalid_url(self):
        hunter = Hunter("http://localhost:5000/dfsfdsdf")
        with self.assertRaises(Exception):
            hunter.find()


@patch("emailshunter.hunter.get_resource")
class HuntManagerTest(WebsiteTestCase):

    @patch_get_resource(pass_mock=True)
    def test_respects_max_depth(self, get_mock):
        hm = HuntManager("http://localhost:5000/", max_depth=2)
        result = hm.run()
        visited_urls = [ call[0][0] for call in get_mock.call_args_list ]
        self.assertFalse(any("articles" in url for url in visited_urls))


    # @patch_get_resource(pass_mock=True)
    # def test_for_not_visiting_the_same_page(self, get_mock):
    #     hm = HuntManager("http://localhost:5000/")
    #     result = hm.run()
    #     import pdb; pdb.set_trace()        
