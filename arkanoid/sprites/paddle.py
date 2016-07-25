import itertools
import logging
import math

import pygame

from arkanoid.event import receiver
from arkanoid.util import (load_png,
                           load_png_sequence)

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
        self._speed = speed

        # The current movement in pixels. A negative value will trigger the
        # paddle to move left, a positive value to move right.
        self._move = 0

        # This toggles visibility of the paddle.
        self.visible = True

        # Load the default paddle image.
        self.image, self.rect = load_png('paddle.png')

        # Create the area the paddle can move laterally in.
        screen = pygame.display.get_surface().get_rect()
        self.area = pygame.Rect(screen.left + left_offset,
                                screen.height - bottom_offset,
                                screen.width - left_offset - right_offset,
                                self.rect.height)
        # Position the paddle.
        self.rect.center = self.area.center

        # Used when the paddle needs to explode.
        self.exploding_animation = None

        # A list of no-args callables that will be called on ball collision.
        self.ball_collide_callbacks = []

        # The current paddle state.
        self._state = NormalState(self)

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
            if self._move:
                newpos = self.rect.move(self._move, 0)
                if self._area_contains(newpos):
                    # But only update the position of the paddle if it's
                    # within the movable area.
                    self.rect = newpos
                else:
                    # The new position is not within the screen area based on
                    # current speed, which might leave a small gap. Adjust the
                    # speed until we match the paddle up with the edge of the
                    # game area exactly.
                    while self._move != 0:
                        if self._move < 0:
                            self._move += 1
                        else:
                            self._move -= 1

                        newpos = self.rect.move(self._move, 0)
                        if self._area_contains(newpos):
                            self.rect = newpos
                            break

    def _area_contains(self, newpos):
        return self.area.collidepoint(newpos.midleft) and \
               self.area.collidepoint(newpos.midright)

    def transition(self, state):
        """Transition to the specified state.

        Note that this is a request to transition, notifying an existing state
        to exit, before switching to the new state.

        Args:
            state:
                The state to transition to.
        """
        def on_complete():
            # Switch the state on state exit.
            self._state = state

        self._state.exit(on_complete)

    def move_left(self):
        """Tell the paddle to move to the left by the speed set when the
        paddle was initialised."""
        # Set the offset to negative to move left.
        self._move = -self._speed

    def move_right(self):
        """Tell the paddle to move to the right by the speed set when the
        paddle was initialised."""
        # A positive offset to move right.
        self._move = self._speed

    def stop(self):
        """Tell the paddle to stop moving."""
        self._move = 0

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

    def on_ball_collide(self, paddle):
        """Called when the ball collides with the paddle.

        This implementation delegates to the instance level
        ball_collide_callbacks list. To monitor for ball collisions, add
        a callback to that list.

        Args:
            paddle:
                The paddle that was struck.
        """
        for callback in self.ball_collide_callbacks:
            callback()

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
        angles = 220, 245, 260, 280, 295, 320

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
    logic should reside, such as animation behaviour.

    The exit() method is called before a transition to a new state. States
    should perform any exit behaviour here, such as triggering an animation 
    to return to normal, before calling the no-args on_complete callback.
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

    def exit(self, on_complete):
        """Sub-states must implement this to perform any behaviour that should
        happen just before the state transitions to some other state.

        When the exit behaviour is completed, sub-states must call the no-args
        on_complete callable.

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

        self._image_loaded = False
        self._image_sequence = load_png_sequence('paddle')
        self._animation = None
        self._update_count = 0

    def update(self):
        if not self._image_loaded:
            pos = self.paddle.rect.center
            self.paddle.image, self.paddle.rect = load_png('paddle.png')
            self.paddle.rect.center = pos
            self._image_loaded = True

        # Pulsate the paddle lights.
        if self._update_count % 100 == 0:
            self._animation = itertools.chain(self._image_sequence,
                                              reversed(self._image_sequence))
            self._update_count = 0
        elif self._animation:
            try:
                if self._update_count % 8 == 0:
                    self.paddle.image, _ = next(self._animation)
            except StopIteration:
                self._animation = None

        self._update_count += 1

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

    def exit(self, on_complete):
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
        self._game = game

        # Load the images/rects for converting to a laser paddle.
        self._image_sequence = load_png_sequence('paddle_laser')
        self._laser_anim = iter(self._image_sequence)

        # Whether we're converting to or from a laser paddle.
        self._to_laser, self._from_laser = True, False

        # Track the number of laser bullets currently in the air.
        self._bullets = []

        # Exit callback.
        self._on_complete = lambda: None

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

    def exit(self, on_complete):
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
        """Event handler that fires bullets from the paddle when the 
        spacebar is pressed.
        """
        if event.key == pygame.K_SPACE:
            self._bullets = [bullet for bullet in self._bullets if
                             bullet.visible]
            # Fire the bullets, only allowing max 4 in the air at once.
            if len(self._bullets) < 3:
                # Create the bullet sprites. We fire two bullets at once.
                left, top = self.paddle.rect.bottomleft
                bullet1 = LaserBullet(self._game, position=(left + 7, top))
                bullet2 = LaserBullet(self._game, position=(
                    left + self.paddle.rect.width - 7, top))

                self._bullets.append(bullet1)
                self._bullets.append(bullet2)

                # Allow the bullets to be displayed.
                self._game.sprites.append(bullet1)
                self._game.sprites.append(bullet2)

                # Release them.
                bullet1.release()
                bullet2.release()


class LaserBullet(pygame.sprite.Sprite):
    """A bullet fired from the laser paddle."""

    def __init__(self, game, position, speed=15):
        """Initialise the laser bullets.

        Args:
            game:
                The running Game instance.
            position:
                The position the bullet starts from.
            speed:
                The speed at which the bullet travels.
        """
        super().__init__()
        # Load the bullet and its rect.
        self.image, self.rect = load_png('laser_bullet.png')

        self._game = game
        self._position = position
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
        self.rect.midbottom = self._position
        self.visible = True

    def update(self):
        """Animate the laser bullet moving upwards, and handle any collisions
        with bricks.
        """
        # Only update if we're still visible.
        if self.visible:
            # Calculate the new position.
            self.rect = self.rect.move(0, -self._speed)

            if not self._game.round.edges.top.rect.colliderect(self.rect):
                # We haven't collided with the top of the game area, so
                # check whether we've collided with a brick.
                visible_bricks = [brick for brick in self._game.round.bricks
                                  if brick.visible]
                collided = pygame.sprite.spritecollide(self, visible_bricks,
                                                       False)

                if collided:
                    # We've collided with a brick.
                    brick = collided[0]
                    # The game's score is not increased when a laser destroys
                    # a brick.
                    brick.value = 0
                    # Powerups aren't released when laser destroys a brick.
                    brick.powerup_cls = None
                    # Invoke the collision callback.
                    # TODO: the on_collide callback should probably accept a
                    # sprite rather than a brick specifically. The callback
                    # can then decide whether this sprite should be destroyed
                    # and return boolean to indicate that here.
                    self._game.on_brick_collide(brick)

                    # Since we've collided, we're no longer visible.
                    self.visible = False
            else:
                # We've collided with the top edge of the game area.
                self.visible = False
