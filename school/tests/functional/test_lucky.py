from school.tests import *

class TestLuckyController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='lucky', action='index'))
        # Test response...
