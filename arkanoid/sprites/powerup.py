import itertools
import logging

import pygame

from arkanoid.sprites import paddle
from arkanoid.utils import load_png

LOG = logging.getLogger(__name__)


class PowerUp(pygame.sprite.Sprite):
    """A PowerUp represents the capsule that falls from a brick and enhances
    the game in some way when it collides with the paddle.

    This is an abstract base class that holds functionality common to all
    concrete powerups. Concrete subclasses must implement _activate() to
    perform the powerup specific action and also deactivate() to undo the
    action. It is important that all powerup initialisation takes place in
    _activate() and not in the __init__() method to ensure that actions
    happen at the right time.
    """

    # The speed the powerup falls from a brick.
    _DEFAULT_FALL_SPEED = 3

    def __init__(self, game, brick, pngs, speed=_DEFAULT_FALL_SPEED):
        """
        Initialise a new PowerUp.

        Args:
            game:
                The current game instance.
            brick:
                The brick that triggered the powerup to drop.
            pngs:
                Iterator of png filenames used to animate the powerup. These
                will be loaded from the data/graphics directory and must be
                supplied in the correct order.
            speed:
                Optional speed at which the powerup drops. Default 3 pixels
                per frame.
        """
        super().__init__()
        self.game = game
        self._speed = speed
        self._animation = itertools.cycle([load_png(png)[0] for png in pngs])
        self._animation_start = 0

        self.image = None
        # Position the powerup by the position of the brick which contained it.
        self.rect = pygame.Rect(brick.rect.bottomleft,
                                (brick.rect.width, brick.rect.height))

        # The area within which the powerup falls.
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()

        # Visibility toggle.
        self.visible = True

    def update(self):
        # Move down by the specified speed.
        self.rect = self.rect.move(0, self._speed)

        if self._area.contains(self.rect):
            if self._animation_start % 2 == 0:
                # Animate the powerup.
                self.image = next(self._animation)

            # Check whether the powerup has collided with the paddle.
            if self.rect.colliderect(self.game.paddle.rect):
                # We've collided, so first check whether there is an
                # existing active powerup in the game, and deactivate if so.
                if self.game.active_powerup:
                    self.game.active_powerup.deactivate()
                # Activate ourselves.
                self._activate()
                # Set ourselves as the active powerup in the game.
                self.game.active_powerup = self
                # No need to display ourself anymore.
                self.game.powerups.remove(self)
                self.visible = False  # TODO: is this needed (and below)?
            else:
                # Keep track of the number of update cycles for animation
                # purposes.
                self._animation_start += 1

        else:
            # We're no longer on the screen.
            self.game.powerups.remove(self)
            self.visible = False

    def _activate(self):
        """Abstract hook method which should be overriden by concrete
        powerup subclasses to perform the powerup specific action.
        """
        raise NotImplementedError('Subclasses must implement _activate()')

    def deactivate(self):
        """Deactivate the current powerup by returning the game state back
        to what it was prior to the powerup taking effect.
        """
        raise NotImplementedError('Subclasses must implement deactivate()')


class ExtraLifePowerUp(PowerUp):
    """This PowerUp applies an extra life to the game when it collides with
    the Paddle.
    """

    _PNG_FILES = 'powerup_extra_life.png',

    def __init__(self, game, brick):
        super().__init__(game, brick, self._PNG_FILES)

    def _activate(self):
        # Add an extra life to the game.
        self.game.lives += 1

    def deactivate(self):
        """Deactivate the current powerup by returning the game state back
        to what it was prior to the powerup taking effect. For the
        ExtraLifePowerUp, this is a no-op.
        """
        pass


class SlowBallPowerUp(PowerUp):
    """This PowerUp causes the ball to move more slowly."""

    _PNG_FILES = 'powerup_slow_ball.png',
    # The ball will assume this base speed when the powerup is activated.
    _SLOW_BALL_SPEED = 5  # Pixels per frame.

    def __init__(self, game, brick):
        super().__init__(game, brick, self._PNG_FILES)

        self._orig_speed = None

    def _activate(self):
        # Remember the original speed of the ball.
        self._orig_speed = self.game.ball.base_speed

        # Slow the ball down.
        self.game.ball.speed = self._SLOW_BALL_SPEED
        self.game.ball.base_speed = self._SLOW_BALL_SPEED

    def deactivate(self):
        """Deactivate the SlowBallPowerUp by returning the ball back to
        its original speed."""
        self.game.ball.speed = self._orig_speed
        self.game.ball.base_speed = self._orig_speed


class ExpandPowerUp(PowerUp):
    """This PowerUp expands the paddle."""

    _PNG_FILES = 'powerup_expand.png',

    def __init__(self, game, brick):
        super().__init__(game, brick, self._PNG_FILES)

    def _activate(self):
        self.game.paddle.next_state = paddle.WideState

    def deactivate(self):
        """Deactivate the ExpandPowerUp by returning the paddle back to
        its original size."""
        self.game.paddle.state.exit()
