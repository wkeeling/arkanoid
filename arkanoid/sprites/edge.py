import pygame

from arkanoid.util import (load_png,
                           load_png_sequence)

# Constants identifying a particular door in the top edge.
DOOR_TOP_LEFT = 'door_top_left'
DOOR_TOP_RIGHT = 'door_top_right'

# Map of doors to their x,y coordinates. The coordinates identify the
# top left corner of the door.
COORDS = {DOOR_TOP_LEFT: (100, 178),
          DOOR_TOP_RIGHT: (408, 178)}


class TopEdge(pygame.sprite.Sprite):
    """The top edge of the game area."""

    def __init__(self):
        super().__init__()

        self.image, self.rect = load_png('edge_top')
        self._door_open_animation = None
        self._door_close_animation = None
        self._on_open = None

        self._update_count = 0

        self.visible = True

    def update(self):
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
                self._on_open()

    def _animate_close_door(self):
        if self._update_count % 4 == 0:
            try:
                self.image, _ = next(self._door_close_animation)
            except StopIteration:
                self._door_close_animation = None

    def open_door(self, door, on_open):
        self._door_open_animation = iter(load_png_sequence(door))
        self._door_close_animation = None
        self._on_open = lambda: on_open(COORDS[door])

    def close_door(self, door):
        self._door_close_animation = iter(reversed(load_png_sequence(door)))
        self._door_open_animation = None


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
