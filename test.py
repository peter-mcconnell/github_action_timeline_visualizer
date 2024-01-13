import unittest
import os

from steps import parse_log

class TestParsing(unittest.TestCase):
    def test_parse(self):
        with open("logs.zip", "rb") as f:
            content = f.read()
            time_action_pairs = parse_log(content)
            expected_action_pairs = []
            assert(time_action_pairs == expected_action_pairs)
