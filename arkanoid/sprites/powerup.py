import itertools
import logging
import math

import pygame

from arkanoid.event import receiver
from arkanoid.sprites.paddle import (LaserState,
                                     NormalState,
                                     WideState)
from arkanoid.utils.util import load_png_sequence

LOG = logging.getLogger(__name__)

# The speed the powerup falls from a brick.
DEFAULT_FALL_SPEED = 3


class PowerUp(pygame.sprite.Sprite):
    """A PowerUp represents the capsule that falls from a brick and enhances
    the game in some way when it collides with the paddle.

    This is an abstract base class that holds functionality common to all
    concrete powerups. All important powerup initialisation should
    take place in _activate() and not in the __init__() method to ensure
    that actions happen at the right time.
    """

    def __init__(self, game, brick, png_prefix, speed=DEFAULT_FALL_SPEED):
        """
        Initialise a new PowerUp.

        Args:
            game:
                The current game instance.
            brick:
                The brick that triggered the powerup to drop.
            png_prefix:
                The png file prefix that will be used to load the image
                sequence for the powerup animation.
            speed:
                Optional speed at which the powerup drops. Default 3 pixels
                per frame.
        """
        super().__init__()
        self.game = game
        self._speed = speed
        self._animation = itertools.cycle(
            image for image, _ in load_png_sequence(png_prefix))
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
            if self._animation_start % 4 == 0:
                # Animate the powerup.
                self.image = next(self._animation)

            # Check whether the powerup has collided with the paddle.
            if self.rect.colliderect(self.game.paddle.rect):
                # We've collided, so check whether it is appropriate for us
                # # to activate.
                if self._can_activate():
                    # If there is already an active powerup in the game,
                    # deactivate that first.
                    if self.game.active_powerup:
                        self.game.active_powerup.deactivate()
                    # Carry out the powerup specific activation behaviour.
                    self._activate()
                    # Set ourselves as the active powerup in the game.
                    self.game.active_powerup = self
                # No need to display ourself anymore.
                self.game.sprites.remove(self)
                self.visible = False
            else:
                # Keep track of the number of update cycles for animation
                # purposes.
                self._animation_start += 1

        else:
            # We're no longer on the screen.
            self.game.sprites.remove(self)
            self.visible = False

    def _activate(self):
        """Abstract hook method which should be overriden by concrete
        powerup subclasses to perform the powerup specific action.
        """
        raise NotImplementedError('Subclasses must implement _activate()')

    def _can_activate(self):
        """Whether it is appropriate for the powerup to activate given
        current game state.

        Returns:
            True if appropriate to activate, false otherwise.
        """
        if self.game.paddle.exploding or not self.game.paddle.visible:
            # Don't activate when the paddle is exploding or hidden.
            return False
        return True

    def deactivate(self):
        """Deactivate the current powerup by returning the game state back
        to what it was prior to the powerup taking effect.
        """
        raise NotImplementedError('Subclasses must implement deactivate()')


class ExtraLifePowerUp(PowerUp):
    """This PowerUp applies an extra life to the game when it collides with
    the Paddle.
    """

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_life')

    def _activate(self):
        """Add an extra life to the game."""
        self.game.lives += 1

    def deactivate(self):
        """Deactivate the current powerup by returning the game state back
        to what it was prior to the powerup taking effect. For the
        ExtraLifePowerUp, this is a no-op.
        """
        pass


class SlowBallPowerUp(PowerUp):
    """This PowerUp causes the ball(s) to move more slowly."""

    # The ball will assume this base speed when the powerup is activated.
    _SLOW_BALL_SPEED = 6  # Pixels per frame.

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_slow')

        self._orig_speed = None

    def _activate(self):
        """Slow the ball(s) down."""
        # Remember the original speed of the ball.
        self._orig_speed = self.game.ball.base_speed

        # Slow the balls down.
        for ball in self.game.balls:
            ball.speed = self._SLOW_BALL_SPEED
            ball.base_speed = self._SLOW_BALL_SPEED

    def deactivate(self):
        """Deactivate the SlowBallPowerUp by returning the ball(s) back to
        their original speed."""
        for ball in self.game.balls:
            ball.speed = self._orig_speed
            ball.base_speed = self._orig_speed


class ExpandPowerUp(PowerUp):
    """This PowerUp expands the paddle."""

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_expand')

    def _activate(self):
        """Tell the paddle that we want to transition to WideState next."""
        # Increase the speed of the ball(s) slightly now the player has the
        # advantage of a wider paddle.
        self.game.paddle.transition(WideState(self.game.paddle))
        for ball in self.game.balls:
            ball.base_speed += 1

    def deactivate(self):
        """Deactivate the ExpandPowerUp by returning the paddle back to
        its original size."""
        self.game.paddle.transition(NormalState(self.game.paddle))
        for ball in self.game.balls:
            ball.base_speed -= 1

    def _can_activate(self):
        can_activate = super()._can_activate()
        if can_activate:
            # Don't activate if the active powerup is already expand.
            can_activate = not isinstance(self.game.active_powerup,
                                          self.__class__)
        return can_activate


class LaserPowerUp(PowerUp):
    """This PowerUp allows the paddle to fire a laser beam.

    Firing is controlled with the spacebar.
    """

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_laser')

    def _activate(self):
        """Tell the paddle that we want to transition to LaserState next."""
        # Increase the speed of the ball(s) slightly now the player has the
        # advantage of the laser.
        self.game.paddle.transition(LaserState(self.game.paddle, self.game))
        for ball in self.game.balls:
            ball.base_speed += 1

    def deactivate(self):
        """Deactivate the LaserPowerUp by turning the paddle back to a
        normal paddle."""
        self.game.paddle.transition(NormalState(self.game.paddle))
        for ball in self.game.balls:
            ball.base_speed -= 1

    def _can_activate(self):
        can_activate = super()._can_activate()
        if can_activate:
            # Don't activate if the active powerup is already laser.
            can_activate = not isinstance(self.game.active_powerup,
                                          self.__class__)
        return can_activate


class CatchPowerUp(PowerUp):
    """This PowerUp allows the paddle to catch a ball.

    A ball is released by pressing the spacebar.
    """

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_catch')

    def _activate(self):
        """Add the ability to catch a ball when it collides with the
        paddle.
        """
        self.game.paddle.ball_collide_callbacks.append(self._catch)

        # Monitor for spacebar presses to release a caught ball.
        receiver.register_handler(pygame.KEYUP, self._release_ball)

    def deactivate(self):
        """Deactivate the CatchPowerUp from preventing the paddle from
        catching the ball.
        """
        self.game.paddle.ball_collide_callbacks.remove(self._catch)
        receiver.unregister_handler(self._release_ball)
        for ball in self.game.balls:
            ball.release()  # Release a currently caught ball.

    def _release_ball(self, event):
        """Release a caught ball when the spacebar is pressed."""
        if event.key == pygame.K_SPACE:
            for ball in self.game.balls:
                ball.release()

    def _catch(self, ball):
        """Catch the a when it collides with the paddle.
        Args:
            ball:
                The ball to be caught.
        """
        # Work out the position of the ball relative to the paddle.
        pos = (ball.rect.bottomleft[0] - self.game.paddle.rect.topleft[0],
               -ball.rect.height)
        ball.anchor(self.game.paddle, pos)


class DuplicatePowerUp(PowerUp):
    """This powerup causes the ball(s) to split into multiple duplicate balls.
    """

    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_duplicate')

    def _activate(self):
        """Create 2 duplicate balls from each existing ball in the game.

        The dupliate balls have the same speed as the existing ball, but
        slightly differing angles so they all split away from each other.
        """

        # The relative angle at which a clone will split away from the original
        # ball.
        split_angle = 0.4  # Radians

        for ball in list(self.game.balls):
            # Capture the current attributes of the ball.
            start_pos = ball.rect.center

            # Clone the ball twice, with a varying start angle.
            start_angle = ball.angle + split_angle
            if start_angle > 2 * math.pi:
                start_angle -= 2 * math.pi

            ball1 = ball.clone(start_pos=start_pos,
                               start_angle=start_angle)

            start_angle = abs(ball.angle - split_angle)

            ball2 = ball.clone(start_pos=start_pos,
                               start_angle=start_angle)

            # Tell the game about the new balls.
            self.game.balls.append(ball1)
            self.game.balls.append(ball2)

            # Allow them to be displayed.
            self.game.sprites.append(ball1)
            self.game.sprites.append(ball2)

    def deactivate(self):
        # No specific deactivation for this powerup. Once duplicate balls are
        # in play, they just remain in play until they go off-screen.
        pass


class WarpPowerUp(PowerUp):
    """This powerup causes a warp gate to appear through which the Vaus can
    transport to the next level.
    """
    def __init__(self, game, brick):
        super().__init__(game, brick, 'powerup_warp')
