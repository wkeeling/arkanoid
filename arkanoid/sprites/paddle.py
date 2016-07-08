import itertools
import logging
import math

import pygame

from arkanoid.event import receiver
from arkanoid.util import (load_png,
                           load_png_sequence)


__all__ = 'Paddle', 'NORMAL', 'WIDE', 'LASER'

LOG = logging.getLogger(__name__)


class Paddle(pygame.sprite.Sprite):
    """The movable paddle (a.k.a the "Vaus") used to control the ball to
    prevent it from dropping off the bottom of the screen."""

    def __init__(self, left_offset=0, right_offset=0, bottom_offset=0,
                 speed=10):
        """
        Create a new Paddle instance.

        The paddle will travel the entire width of the screen, unless the
        left and right offsets are specified which can restrict its travel.
        A bottom offset can also be supplied which defines how far from the
        bottom of the screen the paddle floats.

        Args:
            left_offset:
                Optional offset in pixels from the left of the screen that
                will restrict the maximum travel of the paddle.
            right_offset:
                Optional offset in pixels from the right of the screen that
                will restrict the maximum travel of the paddle.
            bottom_offset:
                The distance the paddle sits above the bottom of the screen.
            speed:
                Optional speed of the paddle in pixels per frame.
        """
        super().__init__()

        # The speed of the paddle movement in pixels per frame.
        self.speed = speed

        # This toggles visibility of the paddle.
        self.visible = True

        # Load the paddle image and its rect.
        self.image, self.rect = load_png('paddle.png')

        # Create the area the paddle can move within.
        screen = pygame.display.get_surface().get_rect()
        self.area = pygame.Rect(screen.left + left_offset,
                                screen.height - bottom_offset,
                                screen.width - left_offset - right_offset,
                                self.rect.height)
        # Position the paddle.
        self.rect.center = self.area.center

        # The current movement in pixels. A negative value will trigger the
        # paddle to move left, a positive value to move right.
        self.move = 0

        # The current paddle state.
        self._state = NormalState(self)

        # Used when the paddle needs to explode.
        self.exploding_animation = None

    def update(self):
        """Update the state of the paddle."""
        # Delegate to our active state.
        self._state.update()

        if self.exploding_animation:
            # Do the exploding animation.
            self.exploding_animation.update()
        else:
            # We're not exploding, so continuously move the paddle when the
            # offset is non-zero.
            if self.move:
                newpos = self.rect.move(self.move, 0)
                if self._area_contains(newpos):
                    # But only update the position of the paddle if it's
                    # within the movable area.
                    self.rect = newpos
                else:
                    # The new position is not within the screen area based on
                    # current speed, which might leave a small gap. Adjust the
                    # speed until we match the paddle up with the edge of the
                    # game area exactly.
                    while self.move != 0:
                        if self.move < 0:
                            self.move += 1
                        else:
                            self.move -= 1

                        newpos = self.rect.move(self.move, 0)
                        if self._area_contains(newpos):
                            self.rect = newpos
                            break

    def _area_contains(self, newpos):
        return self.area.collidepoint(newpos.midleft) and \
                        self.area.collidepoint(newpos.midright)

    def transition(self, state, *args):
        """Transition to the specified state, as represented by the state
        class.

        Note that this is a request to transition, notifying an existing state
        to exit, before initialising and applying the new state.

        Args:
            state:
                The state class to transition to.
            args:
                Additional arguments that may be passed to the state.
        """
        def on_complete():
            # Switch the state on state exit.
            if args:
                self._state = state(self, *args)
            else:
                self._state = state(self)

        self._state.exit(on_complete)

    def move_left(self):
        """Tell the paddle to move to the left by the speed set when the
        paddle was initialised."""
        # Set the offset to negative to move left.
        self.move = -self.speed

    def move_right(self):
        """Tell the paddle to move to the right by the speed set when the
        paddle was initialised."""
        # A positive offset to move right.
        self.move = self.speed

    def stop(self):
        """Tell the paddle to stop moving."""
        self.move = 0

    def reset(self):
        """Reset the position of the paddle to its start position."""
        self.rect.center = self.area.center

    def explode(self, on_complete):
        """Animate a paddle explosion.

        Args:
            on_complete:
                No-args callable that will be called when the explosion
                animation has finished.
        """
        self.exploding_animation = ExplodingAnimation(self, on_complete)

    @staticmethod
    def bounce_strategy(paddle_rect, ball_rect):
        """Implementation of a ball bounce strategy used to calculate
        the angle that the ball bounces off the paddle. The angle
        of bounce is dependent upon where the ball strikes the paddle.

        Note: this function is not tied to the Paddle class but we house it
        here as it seems a reasonable place to keep it.

        Args:
            paddle_rect:
                The Rect of the paddle.
            ball_rect:
                The Rect of the ball.

        Returns:
            The angle of bounce in radians.
        """
        # Logically break the paddle into 6 segments.
        # Each segment triggers a different angle of bounce.
        segment_size = paddle_rect.width // 6
        segments = []

        for i in range(6):
            # Create rectangles for all segments bar the last.
            left = paddle_rect.left + segment_size * i
            if i < 5:
                # These segments are a fixed size.
                segment = pygame.Rect(left, paddle_rect.top, segment_size,
                                      paddle_rect.height)
            else:
                # The last segment makes up what is left of the paddle width.
                segment = pygame.Rect(left, paddle_rect.top,
                                      paddle_rect.width - (segment_size * 5),
                                      paddle_rect.height)
            segments.append(segment)

        # The bounce angles corresponding to each of the 8 segments.
        angles = -130, -115, -100, -80, -65, -50

        # Discover which segment the ball collided with. Just use the first.
        index = ball_rect.collidelist(segments)

        # Look up the angle and convert it to radians, before returning.
        return math.radians(angles[index])


class ExplodingAnimation:
    """Houses the logic to animate a paddle explosion."""

    def __init__(self, paddle, on_complete):
        """Initialise a new ExplodingPaddle with the paddle and a no-args
        callback which gets called once the animation is complete.

        Args:
            paddle:
                The paddle instance.
            on_complete:
                The no-args callback used to notify the caller when the
                animation is complete.
        """
        # Set up the exploding images.
        self._paddle = paddle
        self._image_explode, _ = load_png('paddle_explode.png')
        self._image_orig, _ = load_png('paddle.png')
        self._exploding_animation = itertools.cycle((self._image_explode,
                                                     self._image_orig))
        # The notification callback.
        self._on_explode_complete = on_complete

        # Keep track of update cycles for animation purposes.
        self._cycles = 0

    def update(self):
        """Run the exploding animation."""
        # Run the animation after a short delay.
        if 20 < self._cycles < 110:
            if self._cycles % 2 == 0:
                self._paddle.image = next(self._exploding_animation)
        elif self._cycles > 110:
            # Animation finished.
            self._paddle.image = self._image_orig
            # Unset ourselves.
            self._paddle.exploding_animation = None
            # Notify the client that we're done.
            self._on_explode_complete()
        self._cycles += 1


class PaddleState:
    """A PaddleState represents a particular state of the paddle, in terms
    of its graphics and behaviour.

    This base class is abstract and concrete sub-states should implement
    both the update() and exit() abstract methods. The update() method is
    called repeatedly by the game and is where much of the state specific 
    logic should reside. 
    
    With the exit() method, states should perform any exit specific
    behaviour and then call the on_complete no-args callback to indicate
    that transition to a new state can now occur.
    """

    def __init__(self, paddle):
        """Initialise the PaddleState with the paddle instance.

        The paddle instance is made available as an instance level attribute
        and can be accessed by concrete sub-states to change paddle attriubtes.

        Args:
            paddle:
                The Paddle instance.
        """
        self.paddle = paddle

        LOG.debug('Entered {}'.format(type(self).__name__))

    def update(self):
        """Update the state of the paddle.

        Sub-states must implement this to perform state specific behaviour.
        This method is designed to be called repeatedly.
        """
        raise NotImplementedError('Subclasses must implement update()')

    def exit(self, on_complete=None):
        """Sub-states must implement this to perform any behaviour that should
        happen just before the state transitions to some other state.

        When the exit behaviour is completed, sub-states must call the no-args
        on_complete callable if one has been passed.

        Args:
            on_complete:
                A no-args callable that will be called when the exit behaviour
                has completed.
        """
        raise NotImplementedError('Subclasses must implement exit()')

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({!r})'.format(class_name, self.paddle)


class NormalState(PaddleState):
    """This represents the default appearance of the paddle."""

    def __init__(self, paddle):
        super().__init__(paddle)

        # Set the default paddle graphic.
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = load_png('paddle.png')
        self.paddle.rect.center = pos

    def update(self):
        # Nothing specific to do in normal state.
        pass

    def exit(self, on_complete=None):
        on_complete()


class WideState(PaddleState):
    """This state represents the wide state of the paddle.

    Animation is used to increase the width when the state is created, and
    also to decrease it when the state exits.
    """

    def __init__(self, paddle):
        super().__init__(paddle)

        # Load the images/rects required for the expanding animation.
        self._image_sequence = load_png_sequence('paddle_wide')
        self._animation = iter(self._image_sequence)

        # Whether we're to expand or to shrink.
        self._expand, self._shrink = True, False

        # Exit callback
        self._on_complete = None

    def update(self):
        """Animate the paddle expanding from normal to wide or shrinking
        from wide to normal."""
        if self._expand:
            self._expand_paddle()
        elif self._shrink:
            self._shrink_paddle()

    def _expand_paddle(self):
        try:
            self._convert()
            while (not self.paddle.area.collidepoint(
                    self.paddle.rect.midleft)):
                # Nudge the paddle back inside the game area.
                self.paddle.rect = self.paddle.rect.move(1, 0)
            while (not self.paddle.area.collidepoint(
                    self.paddle.rect.midright)):
                # Nudge the paddle back inside the game area.
                self.paddle.rect = self.paddle.rect.move(-1, 0)
        except StopIteration:
            self._expand = False

    def _shrink_paddle(self):
        try:
            self._convert()
        except StopIteration:
            # State ends.
            self._shrink = False
            self._on_complete()

    def _convert(self):
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = next(self._animation)
        self.paddle.rect.center = pos

    def exit(self, on_complete=None):
        """Trigger the animation to shrink the paddle and exit the state.

        Args:
            on_complete:
                No-args callable invoked when the shrinking paddle animation
                has completed.
        """
        self._shrink = True
        self._on_complete = on_complete
        self._animation = iter(reversed(self._image_sequence))


class LaserState(PaddleState):
    """This state represents a laser paddle which is able to fire bullets
    upwards at the bricks.

    Animation is used to convert from the normal paddle to the laser paddle
    and vice-versa.
    """

    def __init__(self, paddle, game):
        super().__init__(paddle)

        # Create the two bullet sprites.
        self._bullet1 = LaserBullet(paddle,
                                    offset=7,
                                    bricks=game.round.bricks,
                                    on_collide=game.on_brick_collide)
        self._bullet2 = LaserBullet(paddle,
                                    offset=paddle.rect.width - 7,
                                    bricks=game.round.bricks,
                                    on_collide=game.on_brick_collide)

        # Load the images/rects for converting to a laser paddle.
        self._image_sequence = load_png_sequence('paddle_laser')
        self._laser_anim = iter(self._image_sequence)

        # Allow the bullets to be displayed.
        game.other_sprites.append(self._bullet1)
        game.other_sprites.append(self._bullet2)

        # Whether we're converting to or from a laser paddle.
        self._to_laser, self._from_laser = True, False

        # Exit callback
        self._on_complete = None

    def update(self):
        """Animate the paddle from normal to laser, or from laser to normal.

        Once converted to laser, start monitoring for spacebar presses.
        """
        if self._to_laser:
            self._convert_to_laser()
        elif self._from_laser:
            self._convert_from_laser()

    def _convert_to_laser(self):
        try:
            self._convert()
        except StopIteration:
            # Conversion finished.
            self._to_laser = False
            # Start monitoring for spacebar presses for firing bullets.
            receiver.register_handler(pygame.KEYUP, self._fire)

    def _convert_from_laser(self):
        try:
            self._convert()
        except StopIteration:
            # State ends.
            self._from_laser = False
            self._on_complete()

    def _convert(self):
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = next(self._laser_anim)
        self.paddle.rect.center = pos

    def exit(self, on_complete=None):
        """Trigger the animation to return to normal state.

        Args:
            on_complete:
                No-args callable invoked when the laser has converted back
                to a normal paddle.
        """
        self._from_laser = True
        self._on_complete = on_complete
        self._laser_anim = iter(reversed(self._image_sequence))
        # Stop monitoring for spacebar presses now that we're leaving the
        # state.        
        receiver.unregister_handler(self._fire)

    def _fire(self, event):
        if event.key == pygame.K_SPACE:
            # Fire the bullets, but only if they aren't already on the screen.
            # We only allow one pair of bullets to be fired at once.
            if not self._bullet1.visible and not self._bullet2.visible:
                self._bullet1.release()
                self._bullet2.release()


class LaserBullet(pygame.sprite.Sprite):
    """Represent a bullet fired from the laser paddle."""

    def __init__(self, paddle, offset, bricks, on_collide, speed=15):
        """Initialise the laser bullets.

        Args:
            paddle:
                The paddle from which the bullet is fired.
            offset:
                The offset from the left of the paddle from which the bullet
                starts its upwards trajectory.
            bricks:
                The bricks that the bullet might collide with and destroy.
            on_collide:
                A callback that will be invoked when the bullet collides
                with a brick. The callback must accept one argument: the
                brick instance.
            speed:
                The speed at which the bullet travels.
        """
        super().__init__()
        # Load the bullet and its rect.
        self.image, self.rect = load_png.__wrapped__('laser_bullet.png')

        self._paddle = paddle
        self._offset = offset
        self._bricks = bricks
        self._on_collide = on_collide
        self._speed = speed

        # The area within which the bullet is travelling.
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()

        # Whether the bullet is visible.
        # It may not be visible if it went off screen without hitting a brick,
        # or if it hit a brick and was destroyed as a result.
        self.visible = False

    def release(self):
        """Set the bullet in motion from its start point."""
        # Set the start position of the bullet.
        left, top = self._paddle.rect.bottomleft
        self.rect.midbottom = left + self._offset, top
        self.visible = True

    def update(self):
        """Animate the laser bullet moving upwards, and handle any collisions
        with bricks.
        """
        # Only update if we're still visible.
        if self.visible:
            # Calculate the new position.
            self.rect = self.rect.move(0, -self._speed)

            # Check we're on the screen.
            if self._area.contains(self.rect):
                # Check if we've collided with a brick.
                visible_bricks = [brick for brick in self._bricks
                                  if brick.visible]
                index = self.rect.collidelist(
                    [brick.rect for brick in visible_bricks])

                if index > -1:
                    # We've collided with a brick, find out which.
                    brick = visible_bricks[index]
                    # Powerups aren't released when laser destroys a brick.
                    brick.powerup_cls = None
                    # Invoke the collision callback.
                    self._on_collide(brick)

                    # Since we've collided, we're no longer visible.
                    self.visible = False
            else:
                # No longer on the screen.
                self.visible = False


# The different paddle states.
NORMAL = NormalState
WIDE = WideState
LASER = LaserState
