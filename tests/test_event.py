from unittest import TestCase

from arkanoid.event import receiver


class TestEventReceiver(TestCase):

    def test_register_handler(self):
        def handler():
            pass

        receiver.register_handler('foo', handler)

        self.assertIn(handler, receiver._handlers['foo'])

    def test_register_multiple_handlers(self):
        def handler1():
            pass

        def handler2():
            pass

        receiver.register_handler('foo', handler1, handler2)

        self.assertIn(handler1, receiver._handlers['foo'])
        self.assertIn(handler2, receiver._handlers['foo'])

    def test_register_handler_raises_exception_when_no_handler(self):
        with self.assertRaises(AssertionError):
            receiver.register_handler('foo')

    def test_unregister_handler(self):
        def handler():
            pass

        receiver._handlers['test_event'].append(handler)

        receiver.unregister_handler(handler)

        self.assertNotIn(handler, receiver._handlers['test_event'])

    def test_unregister_multiple_handlers(self):
        def handler1():
            pass

        def handler2():
            pass

        receiver._handlers['test_event'] += handler1, handler2

        receiver.unregister_handler(handler1, handler2)

        self.assertNotIn(handler1, receiver._handlers['test_event'])
        self.assertNotIn(handler2, receiver._handlers['test_event'])

    def test_unregister_handler_raises_exception_when_no_handler(self):
        with self.assertRaises(AssertionError):
            receiver.unregister_handler()
