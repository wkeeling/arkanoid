import itertools
import logging
import math

import pygame

from arkanoid.utils import load_png


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
        # The offsets.
        self.left_offset = left_offset
        self.right_offset = right_offset
        self.bottom_offset = bottom_offset

        # The speed of the paddle movement in pixels per frame.
        self.speed = speed

        # Load the paddle image and its rect.
        self.image, self.rect = load_png('paddle.png')

        # This toggles visibility of the paddle.
        self.visible = True

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
        self.state = NormalState(self)

        # The next state to transition to.
        self.next_state = None

    def update(self):
        if self.state.complete and self.next_state:
            # Transition to the next state when current state complete.
            self.state = self.next_state(self)
            self.next_state = None

        # Delegate to our active state.
        self.state.update()

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


class PaddleState:
    """Abstract base class for all paddle states.

    Sub-states should implement both the _do_update() and _do_exit() abstract
    methods. The _do_update() method is where the guts of the state specific
    behaviour is performed.

    In the _do_exit() method, states should perform any exit specific behaviour
    and then set the 'complete' instance attribute to True, to permit the
    transition to a new state.
    """

    def __init__(self, paddle):
        """Initialise the PaddleState with the paddle instance.

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

        This method is designed to be called repeatedly.
        """
        # Continuously move the paddle when the offset is non-zero.
        newpos = self.paddle.rect.move(self.paddle.move, 0)

        if self.paddle.area.contains(newpos):
            # But only update the position of the paddle if it's within
            # the screen area.
            self.paddle.rect = newpos

        # Delegate to the sub-state.
        self._do_update()

    def _do_update(self):
        """Sub-states must implement this to perform state specific behaviour.
        """
        raise NotImplementedError('Subclasses must implement update()')

    def exit(self):
        """Perform any behaviour that should take place before transitioning
        to a new state.
        """
        # By default we always set the next state to NormalState. This might
        # be overriden externally.
        self.paddle.next_state = NormalState

        # Delegate to the sub-state.
        self._do_exit()

    def _do_exit(self):
        """Sub-states must implement this to perform any behaviour that should
        happen just before the state transitions to some other state.

        Sub-states should set the 'complete' instance attribute to True once
        this behaviour is completed.
        """
        raise NotImplementedError('Subclasses must implement _do_exit()')


class NormalState(PaddleState):
    """This is the default state of the paddle."""

    def __init__(self, paddle):
        super().__init__(paddle)

        # We're always in a completed state, ready to transition to
        # a new state.
        self.complete = True

    def _do_update(self):
        # Nothing specific to do in normal state.
        pass

    def _do_exit(self):
        pass


class WideState(PaddleState):
    """This state increases the width of the normal paddle.

    Animation is used to increase the width, and also to decrease it when
    the state exits.
    """

    _PADDLE_IMAGES = ('paddle_expand_1.png',
                      'paddle_expand_2.png',
                      'paddle_expand_3.png')

    def __init__(self, paddle):
        super().__init__(paddle)

        # Save the current position of the paddle.
        self._position = paddle.rect.center

        # Load the images/rects required for the animation.
        self._images = [load_png(img) for img in self._PADDLE_IMAGES]

        # Keep track of the number of times we're updated, in order to
        # animate.
        self._update_count = 0

    def _do_update(self):
        """Animate the paddle expanding from normal to wide."""
        if len(self._images) > 0:
            if self._update_count % 5 == 0:
                self.image, self.rect = self._images.pop(0)
                self.rect.center = self._position
            self._update_count += 1

    def _do_exit(self):
        """Animate the paddle back to its normal size."""
        LOG.debug('Shrinking...')
        self.complete = True


class ExplodingPaddle(pygame.sprite.Sprite):
    """Used to animate a paddle explosion when the paddle misses the ball.

    Note that this does not behave like a normal paddle. It's just an
    animation.
    """

    def __init__(self, paddle, on_complete=None):
        """Initialise a new ExplodingPaddle using an existing Paddle sprite,
        and a no-args callback which notifies the caller when the explosion
        has finished.

        Args:
            paddle:
                The existing Paddle instance.
            on_complete:
                Optional no-args callback which is called when the explosion
                has finished.
        """
        self.image, _ = load_png('paddle_explode.png')
        self.rect = paddle.rect
        self.visible = True

        self._animation = itertools.cycle((self.image, paddle.image))
        self._on_complete = on_complete
        self._explosion_start = 0

    def update(self):
        if self._explosion_start < 90:
            if self._explosion_start % 2 == 0:
                self.image = next(self._animation)
            self._explosion_start += 1
        else:
            if self._on_complete:
                self._on_complete()

    def move_left(self):
        pass

    def move_right(self):
        pass

    def stop(self):
        pass
