import logging
import math
import random

import pygame

from arkanoid.utils.util import load_png

LOG = logging.getLogger(__name__)

TWO_PI = math.pi * 2
HALF_PI = math.pi / 2

# A value will be chosen at random between this and it's negative
# to apply to the angle of bounce for top/bottom/side collisions of the ball.
RANDOM_RANGE = 0.1  # Radians


class Ball(pygame.sprite.Sprite):
    """The ball that bounces around the screen.

    A Ball is aware of the screen, and any sprites on the screen
    that have been added via add_collidable_sprite(). Note that the game
    edges are considered to be collidable sprites.

    The ball will begin its journey using the position and angle specified
    when the ball is initialised. As the ball collides with sprites, its
    angle of bounce will be calculated. Furthermore, its speed may increase
    or decrease but it will never exceed the top_speed.
    When not colliding, the ball will gradually try to settle back to the
    base_speed.

    Once the ball goes off the screen, the no-args off_screen_callback will
    be invoked, if one was set when the ball was initialised.

    See __init__() for further information.
    """

    def __init__(self, start_pos, start_angle, base_speed, top_speed=15,
                 normalisation_rate=0.02,
                 off_screen_callback=None):
        """
        Initialise a new Ball with the given arguments.

        If supplied, the off_screen_callback will be invoked whenever the
        ball leaves the screen. This callable takes a single argument: the
        ball sprite instance.

        Args:
            start_pos:
                The starting coordinates of the ball. A 2 element sequence.
            start_angle:
                The starting angle of the ball in radians.
            base_speed:
                The baseline speed of the ball. Collisions with objects may
                momentarily increase/decrease the speed of the ball, but the
                ball will always try to gradually settle back to the base
                speed.
            top_speed:
                The maximum permitted speed of the ball. Collisions with
                objects may increase the speed of the ball, but the speed
                will never go above the top_speed.
            normalisation_rate:
                The per-frame rate at which the ball is brought back to base
                speed, should the speed have changed due to collision with
                an object.
            off_screen_callback:
                A callable that will be called if the ball goes off the edge
                of the screen. It takes a single argument: the ball sprite
                instance.
        """
        super().__init__()
        self.image, self.rect = load_png('ball')
        self.rect.x, self.rect.y = start_pos
        self.visible = True
        self.speed = base_speed
        self.base_speed = base_speed
        self.normalisation_rate = normalisation_rate
        self.angle = start_angle

        self._start_pos = start_pos
        self._start_angle = start_angle
        self._top_speed = top_speed
        self._off_screen_callback = off_screen_callback
        self._anchor = None

        # The area within which the ball is in play.
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()

        # The sprites the ball can collide with.
        self._collidable_sprites = pygame.sprite.Group()

        # The actions associated with the collidable sprites.
        # This dictionary is keyed by the collidable sprite. The value is
        # a 3-element tuple corresponding to the bounce strategy, speed
        # adjustment and collision callback for that sprite.
        self._collision_data = {}

    def add_collidable_sprite(self, sprite, bounce_strategy=None,
                              speed_adjust=0.0, on_collide=None):
        """Add a sprite that the ball might collide with.

        A bounce strategy can be supplied to override the default bouncing
        behaviour of the ball whenever it strikes the sprite being added.
        The strategy should be a callable that will receive two arguments:
        the Rect of the sprite being struck, and the Rect of the ball. It
        should return the angle of bounce in radians. The angle is measured
        clockwise from the righthand x-axis. Angles should be positive.
        If not supplied, the ball will conform to normal trignometric rules
        when bouncing off the sprite.

        In addition, an optional collision callable can be supplied. This will
        be invoked to perform an action whenever the ball strikes the sprite.
        The callable takes two arguments: the sprite that the ball struck and
        the ball that struck it.

        Args:
            sprite:
                The collidable sprite.
            bounce_strategy:
                Optional callable that determines how the ball should bounce
                when it collides with the sprite. It takes 2 arguments: the
                Rect of the object and the Rect of the ball.
            speed_adjust:
                Optional numeric value that will be used to speed up or slow
                down the the ball. Use a negative value to slow the ball down.
            on_collide:
                Optional callable that will be called when a collision occurs.
                It takes 2 arguments: the sprite the ball struck and the ball
                that struck it.
        """
        self._collidable_sprites.add(sprite)
        self._collision_data[sprite] = (
            bounce_strategy, speed_adjust, on_collide)

    def remove_collidable_sprite(self, sprite):
        """Remove a sprite so that the ball can no longer collide with it.

        If the ball does not already know about the sprite, this method will
        just return without doing anything.

        Args:
            sprite:
                The collidable sprite to remove.
        """
        self._collidable_sprites.remove(sprite)
        try:
            del self._collision_data[sprite]
        except KeyError:
            pass

    def remove_all_collidable_sprites(self):
        """Remove all collidable sprites from the ball."""
        self._collidable_sprites.empty()
        self._collision_data.clear()

    def clone(self, **kwargs):
        """Clone the ball creating a new ball with the same collidable
        sprites as the instance being cloned.

        Because the collidable sprites are shared amongst the ball clones,
        when one ball hits a sprite the other balls know about it.

        This method accepts an optional list of keyword arguments. These, if
        supplied, will override the values of the ball being cloned.

        Args:
            kwargs:
                Optional keyword arguments that will be passed to the
                initialiser of the cloned ball overriding the values of the
                ball being cloned.
        """
        start_pos = kwargs.get('start_pos', self._start_pos)
        start_angle = kwargs.get('start_angle', self._start_angle)
        base_speed = kwargs.get('base_speed', self.base_speed)
        top_speed = kwargs.get('top_speed', self._top_speed)
        normalisation_rate = kwargs.get('normalisation_rate',
                                        self.normalisation_rate)
        off_screen_callback = kwargs.get('off_screen_callback',
                                         self._off_screen_callback)

        ball = Ball(start_pos, start_angle, base_speed, top_speed,
                    normalisation_rate, off_screen_callback)

        for sprite in self._collidable_sprites:
            bounce_strategy, speed_adjust, on_collide = self._collision_data[
                sprite]
            ball.add_collidable_sprite(sprite, bounce_strategy, speed_adjust,
                                       on_collide)

        return ball

    def update(self):
        """Update the ball's position.

        Check whether the ball has collided with anything and if so, update
        its angle and speed and invoke any associated actions.
        """
        # Get the new position of the ball.
        self.rect = self._calc_new_pos()

        if self._area.contains(self.rect):
            if not self._anchor:
                # The ball is still on the screen and is not anchored, so see
                # if it has collided with anything.
                sprites_collided = pygame.sprite.spritecollide(
                    self,
                    (s for s in self._collidable_sprites if s.visible), False)

                if sprites_collided:
                    # Handle the collision.
                    self._handle_collision(sprites_collided)
                else:
                    # No collision. Bring speed back to base.
                    self._normalise_speed()
        else:
            # Ball has gone off the screen.
            # Invoke the callback if we have one.
            if self._off_screen_callback:
                self._off_screen_callback(self)

    def _calc_new_pos(self):
        if self._anchor:
            pos, rel_pos = self._anchor
            try:
                rect = pos.rect
            except AttributeError:
                # A fixed position.
                return pygame.Rect(pos, (self.rect.width, self.rect.height))
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
            offset_x = self.speed * math.cos(self.angle)
            offset_y = self.speed * math.sin(self.angle)

            return self.rect.move(offset_x, offset_y)

    def _handle_collision(self, sprites):
        rects, bounce_strategy = [], None

        for sprite in sprites:
            rects.append(sprite.rect)
            if not bounce_strategy:
                bounce_strategy = self._collision_data[sprite][0]

            if self.speed < self._top_speed:
                # Adjust the speed based on what we collided with.
                self.speed += self._collision_data[sprite][1]

            on_collide = self._collision_data[sprite][2]
            if on_collide:
                # Invoke a collision action if we have one.
                on_collide(sprite, self)

        if len(rects) == 1:
            # Collision with a single object.
            if bounce_strategy:
                # We have a bounce strategy, so use that.
                self.angle = bounce_strategy(rects[0], self.rect)
            else:
                # Use the default calculation for the angle.
                self.angle = self._calc_new_angle(rects)
        else:
            # Collision with more than one object.
            # Use the default calculation for the angle.
            self.angle = self._calc_new_angle(rects)

        LOG.debug('Ball speed: %s', self.speed)

    def _normalise_speed(self):
        """Gradually bring the ball's speed back to the base speed."""
        if self.speed > self.base_speed:
            self.speed -= self.normalisation_rate
        else:
            self.speed += self.normalisation_rate

    def _calc_new_angle(self, rects):
        """Calculate the default angle of bounce of the ball, given a
        sequence of rectangles that the ball collided with.
        """
        tl, tr, bl, br = self._determine_collide_points(rects)

        angle = self.angle

        if [tl, tr, bl, br].count(True) in (1, 3, 4):
            # Ball has collided with a corner, or is fully inside another
            # sprite. Bounce it back in the direction it came from. Note we
            # don't apply any randomness here, as we need the ball to go back
            # in exactly the opposite direction to prevent it from getting
            # stuck if it is inside a sprite.
            LOG.debug('Corner or multipoint collision')
            if self.angle > math.pi:
                angle = self.angle - math.pi
            else:
                angle = self.angle + math.pi
            if [tl, tr, bl, br].count(True) == 1:
                # Add some randomness to corner collisions to prevent bounce
                # loops.
                angle += random.uniform(-RANDOM_RANGE, RANDOM_RANGE)
        else:
            top_collision = tl and tr and self.angle > math.pi
            bottom_collision = bl and br and self.angle < math.pi

            if top_collision or bottom_collision:
                LOG.debug('Top/bottom collision')
                angle = TWO_PI - self.angle
                # Prevent vertical bounce loops by detecting near vertical
                # angles and adjusting the angle of bounce.
                if (TWO_PI - HALF_PI - 0.06) < angle < (
                        TWO_PI - HALF_PI + 0.06):
                    angle += 0.35
                elif (HALF_PI + 0.06) > angle > (HALF_PI - 0.06):
                    angle += 0.35

            else:
                left_collision = (tl and bl and
                                  HALF_PI < self.angle < TWO_PI - HALF_PI)
                right_collision = tr and br and (
                    self.angle > TWO_PI - HALF_PI or self.angle < HALF_PI)

                if left_collision or right_collision:
                    LOG.debug('Side collision')
                    if self.angle < math.pi:
                        angle = math.pi - self.angle
                    else:
                        angle = (TWO_PI - self.angle) + math.pi

                    # Prevent horizontal bounce loops by detecting near
                    # horizontal angles and adjusting the angle of bounce.
                    if math.pi - 0.06 < angle < math.pi + 0.06:
                        angle += 0.35
                    elif angle > TWO_PI - 0.06:
                        angle -= 0.35
                    elif angle < 0.06:
                        angle += 0.35

            # Add a small amount of randomness to the bounce to make it a
            # little more unpredictable, and to prevent the ball from getting
            # stuck in a repeating bounce loop.
            angle += random.uniform(-RANDOM_RANGE, RANDOM_RANGE)

        angle = round(angle, 2)

        LOG.debug('New angle: %s', angle)
        return angle

    def _determine_collide_points(self, rects):
        """Determine which points on the ball have collided with the
        given sequence of rectangles.

        Args:
            rects:
                The sequence of rectagles the ball has collided with.
        Returns:
            A tuple of 4 booleans corresponding to the top left, rop right,
            bottom left and bottom right corners of the ball. True for any
            of these indicates collision.
        """
        tl, tr, bl, br = False, False, False, False

        for rect in rects:
            # Work out which corners of the ball rect are in contact.
            tl = tl or rect.collidepoint(self.rect.topleft)
            tr = tr or rect.collidepoint(self.rect.topright)
            bl = bl or rect.collidepoint(self.rect.bottomleft)
            br = br or rect.collidepoint(self.rect.bottomright)

        if [tl, tr, bl, br].count(True) == 1:
            # Corner collision, so work out whether this is a head on
            # corner collision, or if the ball has hit the corner obliquely.
            # Where oblique, we manually adjust the collide points so that
            # the ball doesn't bounce back in the direction from which it
            # came (a normal corner bounce), but bounces more naturally.
            if tl:
                if self.angle > TWO_PI - HALF_PI:
                    tr = True
                elif self.angle < math.pi:
                    bl = True
            elif tr:
                if math.pi < self.angle < TWO_PI - HALF_PI:
                    tl = True
                elif self.angle < HALF_PI:
                    br = True
            elif bl:
                if self.angle < HALF_PI:
                    br = True
                elif self.angle > math.pi:
                    tl = True
            elif br:
                if math.pi > self.angle > HALF_PI:
                    bl = True
                elif self.angle > TWO_PI - HALF_PI:
                    tr = True

            if [tl, tr, bl, br].count(True) > 1:
                LOG.debug('Readjusting corner collision')

        return tl, tr, bl, br

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
            self.angle = angle
        self.speed = self.base_speed
        self._anchor = None

    def reset(self):
        """Reset the state of the ball back to its starting state."""
        self.rect.midbottom = self._start_pos
        self.speed = self.base_speed
        self.visible = True
        self.angle = self._start_angle
        self._anchor = None
