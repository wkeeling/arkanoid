from collections import defaultdict
import logging

import pygame

LOG = logging.getLogger(__name__)


class EventReceiver:
    """Receive pygame events and dispatch to registered handlers.

    When an event occurs that matches a registered handler then that handler
    is invoked with the event that triggered it. More than one handler can be
    registered for a given event type.
    """

    def __init__(self):
        # Map of event types to handlers.
        self._handlers = defaultdict(list)

    def receive(self):
        """Receive the latest list of pygame events (if any) and dispatch them
        to any registered handlers.
        """
        event_list = pygame.event.get()

        for event in event_list:
            try:
                handlers = self._handlers[event.type]
            except KeyError:
                # No handlers registered for this event.
                pass
            else:
                for handler in handlers:
                    handler(event)

    def register_handler(self, event_type, *handlers):
        """Register one or more event handlers for the given event type.

        Args:
            event_type:
                The pygame event type.
            handlers:
                One or more event handlers. An event handler is a callable that
                will be called when an event of the given type occurs. The
                callable should accept a single argument, which is the event
                itself.
        """
        assert len(handlers) > 0
        LOG.debug('Registering event handler: %s=%s', event_type, handlers)
        self._handlers[event_type] += handlers

    def unregister_handler(self, *handlers):
        """Unregisters one or more event handlers so that they will no longer
        receive events.

        Args:
            handlers:
                One or more event handlers to unregister.
        """
        assert len(handlers) > 0
        for event_type, evt_handlers in self._handlers.items():
            for h in list(evt_handlers):
                if h in handlers:
                    LOG.debug('Unregistering event handler: %s', h)
                    evt_handlers.remove(h)


# The singleton EventDispatcher instance.
receiver = EventReceiver()
