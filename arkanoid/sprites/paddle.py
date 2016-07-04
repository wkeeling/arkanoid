import itertools
import logging
import math

import pygame

from arkanoid.event import dispatcher
from arkanoid.util import load_png


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

        # Setup the event handlers.
        self._register_event_handlers()

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
            newpos = self.rect.move(self.move, 0)

            if self.area.contains(newpos):
                # But only update the position of the paddle if it's within
                # the screen area.
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
                    if self.area.contains(newpos):
                        self.rect = newpos
                        break

    def transition(self, state):
        """Transition to the specified state, as represented by the state
        class.

        Note that this is a request to transition, notifying an existing state
        to exit, before initialising and applying the new state.

        Args:
            state:
                The state class to transition to.
        """
        def on_complete():
            # Switch the state on state exit.
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

    def _register_event_handlers(self):

        def move_left(event):
            if event.key == pygame.K_LEFT:
                self.move_left()
        dispatcher.register_handler(pygame.KEYDOWN, move_left)

        def move_right(event):
            if event.key == pygame.K_RIGHT:
                self.move_right()
        dispatcher.register_handler(pygame.KEYDOWN, move_right)

        def stop(event):
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                self.stop()
        dispatcher.register_handler(pygame.KEYUP, stop)

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
    called repeatedly and is where much of the state specific logic will
    reside. With the exit() method, states should perform any exit specific
    behaviour and then set the 'complete' instance attribute to True, to
    permit the transition to a new state.
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

        # Sub-states must set this to True when they are done (typically
        # in their exit() implementation) so that a transition to a new state
        # can occur.
        self.complete = False

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


class NormalState(PaddleState):
    """This represents the default state of the paddle."""

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
    """This state represents the wider state of the paddle.

    Animation is used to increase the width when the state is created, and
    also to decrease it when the state exits.
    """

    _PADDLE_IMAGES = ('paddle_expand_1.png',
                      'paddle_expand_2.png',
                      'paddle_expand_3.png')

    def __init__(self, paddle):
        super().__init__(paddle)

        # Load the images/rects required for the expanding animation.
        self._expand_anim = iter(load_png(img) for img in self._PADDLE_IMAGES)

        # Load the images/rects required for the expanding animation.
        self._shrink_anim = iter(
            load_png(img) for img in reversed(self._PADDLE_IMAGES))

        # Keep track of the number of times we're updated, in order to
        # animate.
        self._update_count = 0

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
            if self._update_count % 5 == 0:
                pos = self.paddle.rect.center
                self.paddle.image, self.paddle.rect = next(
                    self._expand_anim)
                self.paddle.rect.center = pos
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
        else:
            self._update_count += 1

    def _shrink_paddle(self):
        try:
            if self._update_count % 5 == 0:
                pos = self.paddle.rect.center
                self.paddle.image, self.paddle.rect = next(
                    self._shrink_anim)
                self.paddle.rect.center = pos
        except StopIteration:
            # State ends.
            self._shrink = False
            self._on_complete()
        else:
            self._update_count += 1

    def exit(self, on_complete=None):
        """Trigger the animation to shrink the paddle and exit the state.

        Args:
            on_complete:
                No-args callable invoked when the shrinking paddle animation
                has completed.
        """
        self._shrink = True
        self._on_complete = on_complete


class LaserState:
    pass


# The different paddle states.
NORMAL = NormalState
WIDE = WideState
LASER = LaserState
