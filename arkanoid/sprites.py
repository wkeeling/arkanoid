import itertools
import logging
import math
import random

import pygame

from arkanoid.utils import load_png


LOG = logging.getLogger(__name__)


class Paddle(pygame.sprite.Sprite):
    """The movable paddle (a.k.a the "Vaus") used to control the ball."""

    def __init__(self, left_offset=0, right_offset=0, bottom_offset=0,
                 speed=10):
        """
        Create a new Paddle instance. A paddle travels from left to right
        controlling the ball and keeping it within the screen.

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
        self._area = pygame.Rect(screen.left + left_offset,
                                 screen.height - bottom_offset,
                                 screen.width - left_offset - right_offset,
                                 self.rect.height)
        # Position the paddle.
        self.rect.center = self._area.center

        # The current movement in pixels. A negative value will trigger the
        # paddle to move left, a positive value to move right.
        self._move = 0

    def update(self):
        """Update the position of the paddle when an arrow key is held down."""
        # Continuously move the paddle when the offset is non-zero.
        newpos = self.rect.move(self._move, 0)
        if self._area.contains(newpos):
            # But only update the position of the paddle if it's within
            # the screen area.
            self.rect = newpos

    def move_left(self):
        """Tell the paddle to move to the left by the speed set when the
        paddle was initialised."""
        # Set the offset to negative to move left.
        self._move = -self.speed

    def move_right(self):
        """Tell the paddle to move to the right by the speed set when the
        paddle was initialised."""
        # A positive offset to move right.
        self._move = self.speed

    def stop(self):
        """Tell the paddle to stop moving."""
        self._move = 0

    def reset(self):
        """Reset the position of the paddle to its start position."""
        self.rect.center = self._area.center

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


class Ball(pygame.sprite.Sprite):
    """The ball that bounces around the screen.

    A Ball is aware of the screen, and any collidable objects in the screen
    that have been added via add_collidable_object(). Where no collidable
    objects have been added, a ball will just travel from its start point
    straight off the edge of the screen calling an off_screen_callback if
    one has been set. It is up to clients to add the necessary collidable
    objects to keep the ball within the confines of the screen.

    A Ball will collide with objects that it is told about via
    add_collidable_object(). It will follow normal physics when bouncing
    off an object, but this can be overriden by passing a bounce strategy
    with a collidable object when it is added to the ball. See
    add_collidable_object() for further details.
    """

    def __init__(self, start_pos, start_angle, base_speed, max_speed=15,
                 normalisation_rate=0.02,
                 off_screen_callback=None):
        """
        Initialise a new Ball with the given arguments.

        If supplied, the off_screen_callback will be invoked whenever the
        ball leaves the screen. This is a no-args callable.

        Args:
            start_pos:
                The starting coordinates of the ball.
            start_angle:
                The starting angle of the ball in radians.
            base_speed:
                The baseline speed of the ball. Collisions with objects may
                increase/decrease the speed of the ball, but the speed will
                never fall below the base speed.
            max_speed
                The maximum permitted speed of the ball. Collisions with
                objects may increase the speed of the ball, but the speed
                will never go above the max_speed.
            normalisation_rate:
                The per-frame rate at which the ball is brought back to base
                speed, should the speed have changed due to collision with
                an object.
            off_screen_callback:
                A no-args callable that will be called if the ball goes off
                the edge of the screen.
        """
        super().__init__()
        # Load the ball image and its rect.
        self.image, self.rect = load_png('ball.png')

        # Position the ball.
        self.rect.midbottom = start_pos

        # This toggles visibility of the ball.
        self.visible = True

        # The speed that the ball will always try to settle to.
        self.base_speed = base_speed

        # The ball's current speed, initialised at the base speed.
        self.speed = self.base_speed

        self._start_angle = start_angle
        self._max_speed = max_speed
        self._normalisation_rate = normalisation_rate
        self._off_screen_callback = off_screen_callback

        # The ball's current angle, initialised to the start angle.
        self._angle = start_angle

        # The area within which the ball is in play.
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()

        # The objects the ball can collide with.
        self._collidable_objects = []

        # The position or sprite the ball may be anchored to.
        self._anchor = None

    def add_collidable_object(self, obj, bounce_strategy=None,
                              speed_adjust=0.0, on_collide=None):
        """Add an object that the ball might collide with.

        The object should be a Rect for static objects, or a Sprite for
        animated objects.

        A bounce strategy can be supplied to override the default bouncing
        behaviour of the ball whenever it strikes the object being added.
        The strategy should be a callable that will receive two arguments:
        the Rect of the object being struck, and the Rect of the ball. It
        should return the angle of bounce in radians. If not supplied, the
        ball will conform to normal physics when bouncing off the object.

        In addition, an optional collision callable can be supplied together
        with the object being added. This will  be invoked to perform an
        action whenever the ball strikes the object. The callable takes one
        argument: the object that the ball struck.

        Args:
            obj:
                The collidable object. A Rect for static objects,
                or a Sprite for animated objects.
            bounce_strategy:
                Optional callable that determines how the ball should bounce
                when it collides with the object. It takes 2 arguments: the
                Rect of the object and the Rect of the ball.
            speed_adjust:
                Optional numeric value that will be used to speed up or slow
                down the the ball. Use a negative value to slow the ball down.
            on_collide:
                Optional callable that will be called when a collision occurs.
                It takes 1 argument: the object the ball struck.
        """
        self._collidable_objects.append(
            (obj, bounce_strategy, speed_adjust, on_collide))

    def remove_collidable_object(self, obj):
        """Remove an object so that the ball can no longer collide with it.

        Args:
            obj:
                The collidable object to remove - either the Rect or Sprite.
        """
        self._collidable_objects = [o for o in self._collidable_objects if
                                    o[0] != obj]

    def remove_all_collidable_objects(self):
        """Remove all collidable objects from the ball."""
        self._collidable_objects.clear()

    def update(self):
        """Update the ball. Check whether the ball has collided with
        anything and if so, update its angle and speed and invoke any
        associated actions.
        """
        # Get the new position of the ball.
        self.rect = self._calc_new_pos()

        if self._area.contains(self.rect):
            # The ball is still on the screen.
            # Find out if the ball has collided with anything.
            # We have to get these on the fly, as the rects of sprites
            # change.
            collidable_rects = self._get_collidable_rects()
            indexes = self.rect.collidelistall(collidable_rects)

            if indexes:
                # There's been a collision - find out with what.
                self._handle_collision(collidable_rects, indexes)
            else:
                # No collision. Bring speed back to base.
                self._normalise_speed()
        else:
            # Ball has gone off the screen.
            # Invoke the callback if we have one.
            if self._off_screen_callback:
                self._off_screen_callback()

    def _calc_new_pos(self):
        if self._anchor:
            pos, rel_pos = self._anchor
            try:
                rect = pos.rect
            except AttributeError:
                # A fixed position.
                return pygame.Rect(pos)
            # We're anchored to another sprite.
            if rel_pos:
                # Use the relative position from the sprite's left/top.
                return pygame.Rect(rect.left + rel_pos[0],
                                   rect.top + rel_pos[1], self.rect.width,
                                   self.rect.height)
            # Use the centre of the sprite.
            return rect.center
        else:
            # Move the ball normally based on angle and speed.
            offset_x = self.speed * math.cos(self._angle)
            offset_y = self.speed * math.sin(self._angle)

            return self.rect.move(offset_x, offset_y)

    def _get_collidable_rects(self):
        """Get the Rects of the collidable objects. Note that these have to
        be dynamically obtained, because in the case of sprites the Rects
        are continually changing.
        """
        rects = []
        for obj, _, _, _ in self._collidable_objects:
            try:
                # obj might be a Sprite with a rect attribute
                rects.append(obj.rect)
            except AttributeError:
                # obj is already a rect
                rects.append(obj)
        return rects

    def _handle_collision(self, collidable_rects, indexes):
        objs, rects, actions, speed_adjust = [], [], [], 0

        for i in indexes:
            # Gather up the objects that we've collided with.
            objs.append(self._collidable_objects[i][0])
            rects.append(collidable_rects[i])
            speed_adjust += self._collidable_objects[i][2]
            actions.append(self._collidable_objects[i][3])

        if len(rects) == 1:
            # Collision with a single object.
            bounce_strategy = self._collidable_objects[indexes[0]][1]
            if bounce_strategy:
                # We have a bounce strategy, so use that.
                self._angle = bounce_strategy(rects[0], self.rect)
            else:
                # Use the default calculation for the angle.
                self._angle = self._calc_new_angle(rects)
        else:
            # Collision with more than one object.
            # Use the default calculation for the angle.
            self._angle = self._calc_new_angle(rects)

        for i in range(len(actions)):
            # Invoke the collision callbacks
            on_collide = actions[i]
            if on_collide:
                on_collide(objs[i])

        # Adjust the speed based on what we collided with.
        if self.speed < self._max_speed:
            self.speed += speed_adjust
        LOG.debug('Ball speed: %s', self.speed)

    def _normalise_speed(self):
        """Gradually bring the ball's speed down to the base speed."""
        if self.speed > self.base_speed:
            self.speed -= self._normalisation_rate
        else:
            self.speed += self._normalisation_rate

    def _calc_new_angle(self, rects):
        """Calculate the default angle of bounce of the ball, given a
        sequence of rectangles that the ball collided with.
        """
        if len(rects) == 3:
            # Collision where 3 bricks join causes the ball to bounce back
            # in the direction it originated.
            LOG.debug('3 brick collision')
            angle = self._angle + math.pi
        else:
            # Has to have collided with max 2 objects. Find out how
            # many points of the ball's rect are in contact.
            tl, tr, bl, br = False, False, False, False

            for rect in rects:
                tl = tl or rect.collidepoint(self.rect.topleft)
                tr = tr or rect.collidepoint(self.rect.topright)
                bl = bl or rect.collidepoint(self.rect.bottomleft)
                br = br or rect.collidepoint(self.rect.bottomright)

            if (tl and tr) or (bl and br):
                # Top of the ball has collided with the bottom of an object,
                # or bottom of the ball has collided with the top of an object.
                LOG.debug('Top/bottom collision')
                angle = -self._angle
            elif sum((tl, tr, bl, br)) == 1:
                # Ball has hit the corner of an object - bounce it back in
                # the direction from which it originated.
                LOG.debug('Corner collision')
                angle = self._angle + math.pi
            else:
                # Ball has hit the side of an object.
                LOG.debug('Side collision')
                angle = math.pi - self._angle

        # Add small amount of randomness +/-3 degrees (+/- 0.05 rad)
        angle += random.uniform(-0.05, 0.05)
        LOG.debug('Angle: %s', angle)

        return angle

    def anchor(self, pos, rel_pos=None):
        """Anchor the ball to the supplied position. This may either be
        coords for a fixed position, or a sprite - allowing the ball to be
        fixed to another moving object. When the position is a sprite, a
        relative position on that sprite can also be supplied, otherwise the
        centre of the sprite will be assumed.

        Args:
            pos:
                The position to anchor the ball to. Either a pair of coords
                for a fixed position, or a sprite - when the ball needs to be
                fixed to another moving object.
            rel_pos:
                The position of the ball relative to the left/top coordinates
                of the sprite, when a sprite is passed as the first argument.
        """
        self._anchor = pos, rel_pos

    def release(self, angle=None):
        """Release an anchored ball letting it move freely. The ball will
        be released at its base speed at the last angle calculated, unless
        the optional angle argument is used to override the angle.

        Args:
            angle:
                Optional angle in radians to release the ball at. If not
                specified, the last angle calculated will be used.
        """
        if angle:
            self._angle = angle
        self.speed = self.base_speed
        self._anchor = None


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


class ExpandingPaddle(Paddle):
    """Paddle that is wider than the normal Paddle, and expands to this
    wider size using an animation."""

    _PADDLE_IMAGES = ('paddle_expand_1.png',
                      'paddle_expand_2.png',
                      'paddle_expand_3.png')

    def __init__(self, paddle):
        """Initialise a new ExpandingPaddle based on the supplied Paddle
        instance.

        The supplied paddle will be used to position the expanding paddle.

        Args:
            paddle:
                The original smaller paddle used to position the expanding
                paddle with.
        """
        super().__init__(paddle.left_offset, paddle.right_offset,
                         paddle.bottom_offset, paddle.speed)

        # Save the position of the original paddle.
        self._position = paddle.rect.center

        # Hide the original paddle.
        paddle.visible = False

        # Load the images/rects required for the animation.
        self._images = [load_png(img) for img in self._PADDLE_IMAGES]

        # Keep track of the number of times we're updated, in order to
        # animate.
        self._update_count = 0

    def update(self):
        """Animate the paddle expanding from normal to wide."""
        super().update()

        # TODO: how about moving this whole concept into the Paddle? Makes
        # life easier when asking for paddle.expanded. Also, once
        # ExpandedPaddle in the game, will never be replaced anyway...
        if len(self._images) > 0:
            if self._update_count % 5 == 0:
                self.image, self.rect = self._images.pop(0)
                self.rect.center = self._position
            self._update_count += 1

    def shrink(self):
        """Animate the paddle back to its normal size."""
        LOG.debug('Shrinking...')


class Brick(pygame.sprite.Sprite):
    """A Brick is hit and destroyed by the ball."""

    def __init__(self, colour, destroy_after=1, powerup_cls=None):
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
            destroy_after:
                The number of strikes by the ball necessary to destroy the
                brick (default 1).
            powerup_cls:
                Optional class of a PowerUp that will be used when the ball
                destroys this brick (default None).
        """
        super().__init__()
        self.colour = colour
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

    def is_destroyed(self):
        """Whether the brick is now destroyed and should be removed from the
        game.

        Returns:
            True if the brick is destroyed. False otherwise.
        """
        return self.collision_count >= self._destroy_after

    def animate(self):
        """Trigger animation of this brick."""
        self._animate = 0


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
                self.visible = False
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
        # TODO: below test won't work, because ExpandingPaddle left in the
        # game after deactivation (but still the sprite). Need to test for
        # paddle.expanded or something.
        if not isinstance(self.game.paddle, ExpandingPaddle):
            # Remove the original paddle as a collidable object.
            self.game.ball.remove_collidable_object(self.game.paddle)

            # Substitute the expanding paddle into the game.
            self.game.paddle = ExpandingPaddle(self.game.paddle)

            # Add it as a collidable object.
            # TODO: might need it's own bounce strategy.
            self.game.ball.add_collidable_object(
                self.game.paddle,
                self.game.paddle.bounce_strategy)

    def deactivate(self):
        """Deactivate the ExpandPowerUp by returning the paddle back to
        its original size."""
        self.game.paddle.shrink()

