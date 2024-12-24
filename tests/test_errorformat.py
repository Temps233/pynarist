from unittest import TestCase
from pynarist._errors import PynaristError


class TestErrorFormat(TestCase):
    def test_build_error(self):
        error = PynaristError.new("ABC", 123)
        self.assertEqual(error.__notes__, ["ABC", "123"])
