from school.tests import *

class TestNowController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='now', action='index'))
        # Test response...
