import logging

import pygame

from arkanoid.util import (load_png,
                           load_png_sequence)

LOG = logging.getLogger(__name__)

# Constants identifying a particular door in the top edge.
DOOR_TOP_LEFT = 'door_top_left'
DOOR_TOP_RIGHT = 'door_top_right'

# Map of doors to their x,y coordinates. The coordinates identify the
# top left corner of the door.
COORDS = {DOOR_TOP_LEFT: (115, 150),
          DOOR_TOP_RIGHT: (415, 150)}


class TopEdge(pygame.sprite.Sprite):
    """The top edge of the game area."""

    def __init__(self):
        super().__init__()

        self.image, self.rect = load_png('edge_top')
        self._image_sequence = {
            DOOR_TOP_LEFT: load_png_sequence(DOOR_TOP_LEFT),
            DOOR_TOP_RIGHT: load_png_sequence(DOOR_TOP_RIGHT)
        }
        self._door_open_animation = None
        self._door_close_animation = None
        self._open_queue = []

        self._update_count = 0

        self.visible = True

    def update(self):
        if not self._door_open_animation and not self._door_close_animation:
            if self._open_queue:
                # Have a peek at the front of the queue.
                delay, door, _ = self._open_queue[0]

                if self._update_count >= delay:
                    # The first item in the queue has exceeded its delay so
                    # we can open the door.
                    self._door_open_animation = iter(
                        self._image_sequence[door])

        if self._door_open_animation:
            self._animate_open_door()
        elif self._door_close_animation:
            self._animate_close_door()

        self._update_count += 1

    def _animate_open_door(self):
        if self._update_count % 4 == 0:
            try:
                self.image, _ = next(self._door_open_animation)
            except StopIteration:
                # Now we've opened the door, we can pop the item that
                # triggered it from the front of the queue.
                _, door, on_open = self._open_queue.pop(0)

                # Set up the door close animation.
                self._door_close_animation = iter(
                    reversed(self._image_sequence[door]))
                self._door_open_animation = None

                # Tell the client that the door is now open.
                on_open()

    def _animate_close_door(self):
        if self._update_count % 4 == 0:
            try:
                self.image, _ = next(self._door_close_animation)
            except StopIteration:
                self._door_close_animation = None

    def open_door(self, door, delay, on_open):
        """Open a door after a given delay and then call the on_open
        callback before automatically closing the door after a short delay.

        Args:
            door:
                The door to open.
            delay:
                The delay before opening the door (cycles).
            on_open:
                A callback that will be invoked after the door has opened
                and before it is closed. The callback accepts a single
                argument: a 2-tuple of the x,y coordinates of the door.
        """
        delay += self._update_count
        self._open_queue.append((delay, door, lambda: on_open(COORDS[door])))
        self._open_queue.sort(key=lambda x: x[0])


class SideEdge(pygame.sprite.Sprite):
    """The side edge of the game area."""

    def __init__(self, side):
        """Initialise a new SideEdge specifying which side - either 'left'
        or 'right'.

        Args:
            side:
                The side - either 'left' or 'right'.
        """
        if side not in ('left', 'right'):
            raise AttributeError("Side must be either 'left' or 'right'")

        super().__init__()

        self.image, self.rect = load_png('edge_%s' % side)
        self.visible = True

    def update(self):
        pass
