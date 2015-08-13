# Tests

import unittest

import logger

class Test(unittest.TestCase):
    def test_pick(self):
        self.assertEqual(logger.pick(None, "foo"), "foo")
        self.assertEqual(logger.pick("foo", "bar"), "foo")
