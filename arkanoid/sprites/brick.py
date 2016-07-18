import itertools
import logging

import pygame

from arkanoid.util import load_png

LOG = logging.getLogger(__name__)


class Brick(pygame.sprite.Sprite):
    """A Brick is hit and destroyed by the ball."""

    def __init__(self, colour, value, destroy_after=1, powerup_cls=None):
        """Initialise a new Brick in the specified colour.

        When a Brick is initialised with the specified colour, a file named
        'brick_<colour>.png' will be loaded from the graphics folder and must
        exist. In addition, a Brick will also attempt to load a file called
        'brick_<colour>_anim.png' from the graphics folder which will be used
        to animate the brick when Brick.animate() is called. This file is
        optional, and if it does not exist, then Brick.animate() will have no
        effect.

        Optionally specify the number of strikes by the ball that it takes to
        destroy the brick (default 1) via the destroy_after attribute. Also
        optionally specify the class of a powerup which will fall from the
        brick when the brick is destroyed by the ball - via the powerup_cls
        attribute.

        Args:
            colour:
                The colour of the brick. Note that a png file named
                'brick_<colour>.png' must exist in the graphics folder.
            value:
                The amount to add to the score when this brick is destroyed.
            destroy_after:
                The number of strikes by the ball necessary to destroy the
                brick (default 1).
            powerup_cls:
                Optional class of a PowerUp that will be used when the ball
                destroys this brick (default None).
        """
        super().__init__()
        self.colour = colour
        self.value = value
        # Load the brick graphic.
        self.image, self.rect = load_png('brick_{}.png'.format(colour))

        # Remember the original brick graphic.
        self.image_orig = self.image

        try:
            # Attempt to load the animation graphic.
            image_anim, _ = load_png('brick_{}_anim.png'.format(colour))
        except FileNotFoundError:
            self._animation = None
        else:
            # Set up the animation which cycles between the two images.
            self._animation = itertools.cycle((self.image, image_anim))

        # The number of ball collisions after which the brick is destroyed.
        self._destroy_after = destroy_after

        # The number of ball collisions with this brick.
        self.collision_count = 0

        # The class of the powerup.
        self.powerup_cls = powerup_cls

        # Whether to animate the brick.
        self._animate = None

    def update(self):
        if self._animation and self._animate is not None:
            if self._animate < 30:
                # Animate for 30 cycles.
                if self._animate % 2 == 0:
                    # Swap the images every 2 cycles to animate.
                    self.image = next(self._animation)
                self._animate += 1
            else:
                # Put back the original brick image.
                self.image = self.image_orig
                self._animate = None

    @property
    def visible(self):
        """Whether the brick is still visible based on its collision count,
        or whether it is destroyed and no longer visible.

        Returns:
            True if the brick is visible. False otherwise.
        """
        return self.collision_count < self._destroy_after

    def animate(self):
        """Trigger animation of this brick."""
        self._animate = 0
