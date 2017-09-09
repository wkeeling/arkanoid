import enum
import logging

import pygame

from arkanoid.utils.util import load_png
from arkanoid.utils.util import load_png_sequence

LOG = logging.getLogger(__name__)


class Brick(pygame.sprite.Sprite):
    """A Brick is hit and destroyed by the ball."""

    def __init__(self, brick_colour, round_no, powerup_cls=None):
        """Initialise a new Brick using the specified BrickColour enum.

        When a brick is initialised with the specified BrickColour, a file
        named 'brick_<colour>.png' will be loaded from the graphics folder -
        where <colour> corresponds to the name attribute of the BrickColour
        enum. That file must exist.

        In addition, the initialiser will also attempt to load an image
        sequence named 'brick_<colour>_N.png' from the graphics folder
        which will be used to animate the brick when  Brick.animate() is
        called. This image sequence is optional, and if the files do not
        exist, then triggering Brick.animate() will have no effect.

        The round number must also be supplied which is used to generate the
        score value for certain brcks.

        Lastly, optionally specify the class of a powerup which will fall
        from the brick when the brick is struck by the ball - via the
        powerup_cls attribute.

        Args:
            brick_colour:
                A BrickColour enum instance. A png file named
                'brick_<colour>.png' must exist in the graphics folder where
                <colour> corresponds to the enum name attribute.
            round_no:
                The current round number used to generate the brick score
                value.
            powerup_cls:
                Optional class of a PowerUp that will be used when the ball
                strikes this brick (default None).
        """
        super().__init__()
        self.colour = brick_colour
        # Load the brick graphic.
        self.image, self.rect = load_png('brick_{}'.format(brick_colour.name))

        # Load the images/rects required for any animation.
        self._image_sequence = [image for image, _ in load_png_sequence(
            'brick_{}'.format(brick_colour.name))]
        self._animation = None

        # The number of ball collisions with this brick.
        self.collision_count = 0

        # The class of the powerup.
        self.powerup_cls = powerup_cls

        # The score value for this brick.
        if brick_colour == BrickColour.silver:
            # The score for silver bricks is a product of the brick value
            # and round number.
            self.value = brick_colour.value * round_no
        else:
            self.value = brick_colour.value

        # The number of collisions before the brick gets destroyed.
        if brick_colour == BrickColour.silver:
            self._destroy_after = 2
        elif brick_colour == BrickColour.gold:
            # Gold bricks are never destroyed.
            self._destroy_after = -1
        else:
            self._destroy_after = 1

    def update(self):
        if self._animation:
            try:
                self.image = next(self._animation)
            except StopIteration:
                self._animation = None

    @property
    def visible(self):
        """Whether the brick is still visible based on its collision count,
        or whether it is destroyed and no longer visible.

        Returns:
            True if the brick is visible. False otherwise.
        """
        if self._destroy_after > 0:
            return self.collision_count < self._destroy_after
        return True

    def animate(self):
        """Trigger animation of this brick."""
        self._animation = iter(self._image_sequence)


class BrickColour(enum.Enum):

    """Enumeration of brick colours and their corresponding score value."""

    blue = 100
    cyan = 70
    # Gold bricks have no score because they are indestructable.
    gold = 0
    green = 80
    orange = 60
    pink = 110
    red = 90
    # The score for a silver brick is the value multiplied by the Round number.
    silver = 50
    white = 40
    yellow = 120
