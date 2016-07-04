from collections import defaultdict
import itertools

import pygame


class EventDispatcher:
    """Dispatch pygame events to registered handlers.

    When an event occurs that matches a registered handler then that handler
    is invoked with the event that triggered it. More than one handler can be
    registered for a given event type.
    """

    def __init__(self):
        # Map of event types to handlers.
        self._handlers = defaultdict(list)

    def dispatch(self):
        """Get the latest list of pygame events (if any) and dispatch them
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

    def register_handler(self, event_type, handler):
        """Register an event handler for the given event type.

        Args:
            event_type:
                The pygame event type.
            handler:
                A callable that will be called when an event of the
                given type occurs. The callable should accept a single
                argument, which is the event itself.
        """
        self._handlers[event_type].append(handler)

    def unregister_handler(self, handler):
        """Unregisters the specified event handler so that it will no longer
        receive events.

        Args:
            handler:
                The handler to unregister.
        """
        for event_type, handlers in self._handlers.items():
            for h in list(handlers):
                if h == handler:
                    handlers.remove(h)


# The singleton EventDispatcher instance.
dispatcher = EventDispatcher()
