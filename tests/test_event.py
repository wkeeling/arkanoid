from unittest import TestCase

from arkanoid.event import dispatcher


class TestEventDispatcher(TestCase):

    def test_register_handler(self):
        def handler():
            pass

        dispatcher.register_handler('foo', handler)

        self.assertIn(handler, dispatcher._handlers['foo'])

    def test_register_multiple_handlers(self):
        def handler1():
            pass

        def handler2():
            pass

        dispatcher.register_handler('foo', handler1, handler2 )

        self.assertIn(handler1, dispatcher._handlers['foo'])
        self.assertIn(handler2, dispatcher._handlers['foo'])

    def test_register_handler_raises_exception_when_no_handler(self):
        with self.assertRaises(AssertionError):
            dispatcher.register_handler('foo')

    def test_unregister_handler(self):
        def handler():
            pass

        dispatcher._handlers['test_event'].append(handler)

        dispatcher.unregister_handler(handler)

        self.assertNotIn(handler, dispatcher._handlers['test_event'])

    def test_unregister_multiple_handlers(self):
        def handler1():
            pass

        def handler2():
            pass

        dispatcher._handlers['test_event'] += handler1, handler2

        dispatcher.unregister_handler(handler1, handler2)

        self.assertNotIn(handler1, dispatcher._handlers['test_event'])
        self.assertNotIn(handler2, dispatcher._handlers['test_event'])

    def test_unregister_handler_raises_exception_when_no_handler(self):
        with self.assertRaises(AssertionError):
            dispatcher.unregister_handler()
