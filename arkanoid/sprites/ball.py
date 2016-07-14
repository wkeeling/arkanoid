import logging
import math
import random

import pygame

from arkanoid.util import load_png

LOG = logging.getLogger(__name__)
TWO_PI = math.pi * 2
HALF_PI = math.pi / 2


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

    def __init__(self, start_pos, start_angle, base_speed, top_speed=15,
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
            top_speed
                The maximum permitted speed of the ball. Collisions with
                objects may increase the speed of the ball, but the speed
                will never go above the top_speed.
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

        self._start_pos = start_pos
        self._start_angle = start_angle
        self._top_speed = top_speed
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
        should return the angle of bounce in radians. The angle is measured
        clockwise from the righthand x-axis. Angles should be positive.
        If not supplied, the ball will conform to normal trignometric rules
        when bouncing off the object.

        In addition, an optional collision callable can be supplied together
        with the object being added. This will be invoked to perform an
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
        if self.speed < self._top_speed:
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
        tl, tr, bl, br = False, False, False, False

        for rect in rects:
            # Work out which corners of the ball rect are in contact.
            tl = tl or rect.collidepoint(self.rect.topleft)
            tr = tr or rect.collidepoint(self.rect.topright)
            bl = bl or rect.collidepoint(self.rect.bottomleft)
            br = br or rect.collidepoint(self.rect.bottomright)

        angle = self._angle

        if [tl, tr, bl, br].count(True) in (1, 3, 4):
            # Ball has collided with a corner, or is fully inside another
            # object. Bounce it back in the direction it came from. Note we
            # don't apply any randomness here, as we need the ball to go back
            # in exactly the opposite direction to prevent it from getting
            # stuck inside an object.
            LOG.debug('Corner or multipoint collision')
            if self._angle > math.pi:
                angle = self._angle - math.pi
            else:
                angle = self._angle + math.pi
        else:
            top_collision = tl and tr and self._angle > math.pi
            bottom_collision = bl and br and self._angle < math.pi

            if top_collision or bottom_collision:
                LOG.debug('Top/bottom collision')
                angle = TWO_PI - self._angle
            else:
                left_collision = (tl and bl and
                                  HALF_PI < self._angle < TWO_PI - HALF_PI)
                right_collision = tr and br and (
                    self._angle > TWO_PI - HALF_PI or self._angle < HALF_PI)

                if left_collision or right_collision:
                    LOG.debug('Side collision')
                    if self._angle < math.pi:
                        angle = math.pi - self._angle
                    else:
                        angle = (TWO_PI - self._angle) + math.pi

            # Add a small amount of randomness to the bounce to make it a
            # little more unpredictable, and to prevent the ball from getting
            # stuck in a repeating bounce loop.
            angle += random.uniform(-0.05, 0.05)

        LOG.debug('New angle: %s', angle)

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

    def reset(self):
        """Reset the state of the ball back to its starting state."""
        self.rect.midbottom = self._start_pos
        self.speed = self.base_speed
        self.visible = True
        self._angle = self._start_angle
        self._anchor = None
