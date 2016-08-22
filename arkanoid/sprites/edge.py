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
        self._on_open = None
        self._delay = 0

        self._update_count = 0

        self.visible = True

    def update(self):
        if self._update_count >= self._delay:
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
                self._door_open_animation = None
                self._delay = 0
                self._on_open()

    def _animate_close_door(self):
        if self._update_count % 4 == 0:
            LOG.debug('Animating close door')
            try:
                LOG.debug('setting image')
                self.image, _ = next(self._door_close_animation)
            except StopIteration:
                LOG.debug('door closed')
                self._door_close_animation = None
                self._delay = 0

    def open_door(self, door, delay, on_open):
        LOG.debug('open door triggered')
        self._door_open_animation = iter(self._image_sequence[door])
        self._door_close_animation = None
        self._on_open = lambda: on_open(COORDS[door])
        self._delay = self._update_count + delay

    def close_door(self, door, delay):
        LOG.debug('close door triggered')
        self._door_close_animation = iter(reversed(self._image_sequence[door]))
        self._door_open_animation = None
        self._delay = self._update_count + delay


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
