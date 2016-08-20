import logging

import pygame

from arkanoid.util import load_png_sequence

LOG = logging.getLogger(__name__)


class Alien(pygame.sprite.Sprite):
    """An alien is released from the doors in the top edge and travels
    downwards towards the paddle.

    If it collides with the ball or paddle it is destroyed in an explosion
    animation and increases the game's score. Colliding with a brick or with
    the game edges will just cause the alien to change direction.
    """

    def __init__(self, game):
        super().__init__()

        # Load the images/rects required for the alien.
        self._image_sequence = load_png_sequence('alien_cone')
        self._animation = iter(self._image_sequence)

        # Track the number of update cycles.
        self._update_count = 0

    def update(self):
        pass