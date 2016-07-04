from unittest import TestCase

from arkanoid.event import dispatcher


class TestEventDispatcher(TestCase):

    def test_register_handler(self):
        def handler():
            pass

        dispatcher.register_handler('foo', handler)

        self.assertIn(handler, dispatcher._handlers['foo'])

    def test_unregister_handler(self):
        def handler():
            pass

        dispatcher._handlers['test_event'].append(handler)

        dispatcher.unregister_handler(handler)

        self.assertNotIn(handler, dispatcher._handlers['test_event'])
