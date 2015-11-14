# Tests

import unittest

import logger
import logger.debug
import logger.decorators

class _Object: pass

class Test(unittest.TestCase):

    ### Helper functions

    def test_pick(self):
        self.assertEqual(logger.pick(None, "foo"), "foo")
        self.assertEqual(logger.pick("foo", "bar"), "foo")

        value = {}
        self.assertIs(logger.pick(value, []), value)
        self.assertIs(logger.pick(None, value), value)

    def test_is_dunder(self):
        self.assertTrue(logger.bypassers.is_dunder("__repr__"))
        self.assertTrue(logger.bypassers.is_dunder("__d__"))

        self.assertFalse(logger.bypassers.is_dunder("____"))
        self.assertFalse(logger.bypassers.is_dunder("__spam___"))
        self.assertFalse(logger.bypassers.is_dunder("___foo__"))
        self.assertFalse(logger.bypassers.is_dunder("_"))

    ### Decorators

    def test_instance_bypass(self):
        value = _Object()
        with logger.decorators.instance_bypass(value):
            self.assertTrue(hasattr(value, "bypassed"))
        self.assertFalse(hasattr(value, "bypassed"))

        class C:
            def __init__(self):
                self.called = False
            def __call__(self):
                self.called = True
                return self

        c = C()
        self.assertFalse(c.called)
        with logger.decorators.instance_bypass(value, c):
            self.assertIs(value.bypassed, c)
        self.assertTrue(c.called)

    def test_handle_bypass(self):
        value = _Object()
        class C:
            def _inner(s):
                return value
            inner = logger.decorators.handle_bypass(_inner)

        self.assertIsInstance(C.inner, logger.decorators.handle_bypass)
        c = C()
        self.assertIsNot(C.inner, c.inner)

        self.assertIs(C._inner, C.inner.func)
        self.assertEqual(c._inner, c.inner) # not the same object, but the same state

    def XXX_test_check_bypass(self): # still todo
        value = _Object()
        class C:
            _bp_handler = None
            def _inner(s):
                return value
            inner = logger.decorators.check_bypass(_inner)

    def test_log_usage(self):
        self.assertIsNone(logger.decorators.log_usage._default_handler)
        # still to-do

    ### Debug functions

    def test_get_function(self):
        self.assertIs(logger.debug.get_function(), type(self).test_get_function)
        def inner():
            self.assertIs(logger.debug.get_function(1), type(self).test_get_function)
        inner()

unittest.main()
