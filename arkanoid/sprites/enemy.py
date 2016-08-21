import itertools
import logging
import math
import random

import pygame

from arkanoid.util import load_png_sequence

LOG = logging.getLogger(__name__)

# The speed the enemy sprite moves in pixels/frame.
SPEED = 2

# A value between these two bounds will be randomly selected for the
# duration of travel (i.e. number of frames) in a given direction.
MIN_DURATION = 30
MAX_DURATION = 60

# A value between this and its negative will be chosen at random and then
# added to the direction of the sprite. This ensures some erraticness in the
# sprites' movement.
RANDOM_RANGE = 1.5  # Radians


class Enemy(pygame.sprite.Sprite):
    """An enemy is released from the doors in the top edge and travels
    downwards towards the paddle.

    If it collides with the ball or paddle it is destroyed in an explosion
    animation and increases the game's score. Colliding with a brick or with
    the game edges will just cause the enemy to change direction.
    """

    def __init__(self, game, start_pos):
        super().__init__()
        self._game = game

        # Set up the sequence of images that will animate the enemy sprite.
        self._animation, width, height = self._load_animation_sequence()

        # Set up the rect that defines the starting position of the sprite,
        # and which also defines its dimensions - which must be big enough
        # to fit the largest of the frames in the animation.
        self.rect = pygame.Rect(start_pos, (width, height))
        self.image = None

        # Define the area within which the sprite will move.
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()

        # The current direction of travel of the sprite.
        self._direction = 0

        # The duration which the sprite will travel in a set direction.
        # This is an update count value. When the update count reaches this
        # value, the direction will be recalculated.
        self._duration = 0

        # Track the number of update cycles.
        self._update_count = 0

        # Sprite visibility toggle.
        self.visible = True

    def _load_animation_sequence(self):
        """Load and return the image sequence for the animated sprite, and
        with it, the maximum width and height of the images in the sequence.

        Returns:
            A 3-element tuple: the itertools.cycle object representing the
            animated sequence, the maximum width, the maximum height.
        """
        sequence = load_png_sequence('enemy_cone')
        max_width, max_height = 0, 0

        for image, rect in sequence:
            if rect.width > max_width:
                max_width = rect.width
            if rect.height > max_height:
                max_height = rect.height

        return itertools.cycle(sequence), max_width, max_height

    def update(self):
        if self._update_count % 4 == 0:
            # Animate the sprite.
            self.image, _ = next(self._animation)

        if not self._duration:
            # Calculate a new direction and duration in that direction.
            self._direction = self._calc_direction()
            self._duration = self._update_count + random.choice(
                range(MIN_DURATION, MAX_DURATION))
        elif self._update_count >= self._duration:
            # We've reached the maximum duration in the given direction,
            # so reset in order for the direction to be changed next cycle.
            self._duration = 0

        # Calculate a new position based on the current direction.
        self.rect = self._calc_new_position()

        self._update_count += 1

    def _calc_direction(self):
        """Calculate the direction of travel."""
        paddle_x, paddle_y = self._game.paddle.rect.center
        angle_to_paddle = math.atan2(paddle_y - self.rect.y,
                                     paddle_x - self.rect.x)
        angle_to_paddle += random.uniform(-RANDOM_RANGE, RANDOM_RANGE)
        return angle_to_paddle

    def _calc_new_position(self):
        offset_x = SPEED * math.cos(self._direction)
        offset_y = SPEED * math.sin(self._direction)

        return self.rect.move(offset_x, offset_y)
