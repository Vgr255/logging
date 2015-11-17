#!/usr/bin/env python3
# encoding: utf-8

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
        self.assertFalse(logger.bypassers.is_dunder(""))

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

    def test_attribute(self):
        obj = _Object()
        class C:
            @logger.decorators.attribute
            def attr(self):
                return obj

        self.assertIsInstance(C.attr, logger.decorators.attribute)
        c = C()
        self.assertIs(c.attr(), obj)
        c.attr = "attribute"
        self.assertIsNot(c.attr, obj)
        self.assertEqual(c.attr, "attribute")

        self.assertEqual(repr(C.attr), "<attribute 'attr' of 'C' objects>")
        C.attr.__doc__ = "docstring"
        self.assertEqual(repr(C.attr), "docstring")
        self.assertEqual(C.attr.__name__, "attr")

        class D:
            @logger.decorators.attribute
            def attr(self):
                """Some attribute."""
                return obj

        self.assertEqual(repr(D.attr), "Some attribute.")
        d = D()
        self.assertNotEqual(repr(d.attr), "Some attribute.")

    def test_meta_property(self):
        obj = _Object()
        class C:
            @logger.decorators.MetaProperty
            def attr(cls):
                self.assertIs(cls, C)
                return obj

        c = C()
        self.assertIs(C.attr, obj)
        self.assertIs(c.attr, obj)

        with self.assertRaises(AttributeError):
            c.attr = "attribute"

        with self.assertRaises(AttributeError):
            del c.attr

    def test_desc_property(self):
        obj = _Object()
        class C:
            @logger.decorators.DescriptorProperty
            def attr(inst, cls):
                self.assertIsNone(inst)
                self.assertIs(cls, C)
                return obj

        self.assertIs(C.attr, obj)

        class D:
            @logger.decorators.DescriptorProperty
            def attr(inst, cls):
                self.assertIs(inst, d)
                self.assertIs(cls, D)
                return obj

        d = D()
        self.assertIs(d.attr, obj)

        with self.assertRaises(AttributeError):
            d.attr = "attribute"

        with self.assertRaises(AttributeError):
            del d.attr

    def test_readonly_attribute(self):
        obj = _Object()
        class C:
            def __init__(s):
                s.hello = obj
            @logger.decorators.readonly
            def hello(s):
                pass

        c = C()

        with self.assertRaises(AttributeError):
            c.hello = "hello"

        with self.assertRaises(AttributeError):
            del c.hello

        self.assertIs(obj, c.hello)
        c.__dict__["hello"] = None
        self.assertIs(obj, c.hello)
        del c.__dict__["hello"]
        self.assertIs(obj, c.hello)

    def test_singleton(self):
        class C: pass

        D = logger.decorators.Singleton(C)
        self.assertIsNot(C, D)
        self.assertIsNot(type(C), type(D))
        self.assertIs(type(type(type(D))), logger.decorators.Singleton)
        self.assertIs(D, type(D)())

        with self.assertRaises(TypeError):
            class E(type(D)): pass

    ### Debug functions

    def test_get_function(self):
        self.assertIs(logger.debug.get_function(), type(self).test_get_function)
        def inner():
            self.assertIs(logger.debug.get_function(1), type(self).test_get_function)
        inner()

unittest.main()
