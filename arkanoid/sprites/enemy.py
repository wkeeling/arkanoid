import enum
import itertools
import logging
import math
import random

import pygame

from arkanoid.util import load_png_sequence

LOG = logging.getLogger(__name__)

# The speed the enemy sprite moves in pixels/frame.
SPEED = 2

# A value between these two bounds will be randomly selected for the
# duration of travel (i.e. number of frames) in a given direction.
MIN_DURATION = 30
MAX_DURATION = 60

# A value between this and its negative will be chosen at random and then
# added to the direction of the sprite. This ensures some erraticness in the
# sprites' movement.
RANDOM_RANGE = 1.5  # Radians

TWO_PI = math.pi * 2
HALF_PI = math.pi / 2


class EnemyType(enum.Enum):

    """Enumeration of enemy types to their image sequence prefix and
    score value.
    """

    cone = 'enemy_cone'
    pyramid = 'enemy_pyramid'
    sphere = 'enemy_sphere'
    cube = 'enemy_cube'


class Enemy(pygame.sprite.Sprite):
    """An enemy is released from the doors in the top edge and travels
    downwards towards the paddle.

    It can be told about other sprites it can collide with via
    add_collidable_sprite(). Colliding with another sprite will cause the
    enemy to change direction.
    """

    def __init__(self, enemy_type, paddle, collidable_sprites, on_destroyed):
        super().__init__()
        self._paddle = paddle
        self._on_destroyed = on_destroyed

        # Set up the sequence of images that will animate the enemy sprite.
        self._animation, width, height = self._load_animation_sequence(
            enemy_type.value)

        # Set up the rect that defines the starting position of the sprite,
        # and which also defines its dimensions - which must be big enough
        # to fit the largest of the frames in the animation.
        self.rect = pygame.Rect((0, 0), (width, height))
        self.image = None

        # The exploding animation when we've been struck by the ball or paddle.
        self._explode_animation = None

        # Define the area within which the sprite will move.
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()

        # The sprites in the game that cause the enemy sprite to change
        # direction when it collides with them.
        self._collidable_sprites = pygame.sprite.Group()
        for sprite in collidable_sprites:
            self._collidable_sprites.add(sprite)

        # The current direction of travel of the sprite.
        self._direction = 1.57  # Initialised in downwards direction.

        # The duration which the sprite will travel in a set direction.
        # This is an update count value. When the update count reaches this
        # value, the direction will be recalculated.
        self._duration = 50  # The initial duration of downwards movement.

        # Track the number of update cycles.
        self._update_count = 0

        # Sprite visibility toggle.
        self.visible = True

    def _load_animation_sequence(self, filename_prefix):
        """Load and return the image sequence for the animated sprite, and
        with it, the maximum width and height of the images in the sequence.

        Args:
            filename_prefix:
                The prefix of the image sequence.
        Returns:
            A 3-element tuple: the itertools.cycle object representing the
            animated sequence, the maximum width, the maximum height.
        """
        sequence = load_png_sequence(filename_prefix)
        max_width, max_height = 0, 0

        for image, rect in sequence:
            if rect.width > max_width:
                max_width = rect.width
            if rect.height > max_height:
                max_height = rect.height

        return itertools.cycle(sequence), max_width, max_height

    def update(self):
        """Update the enemy's position, handling any collisions."""
        if self._explode_animation:
            self._explode()
        else:
            if self._update_count % 4 == 0:
                # Animate the sprite.
                self.image, _ = next(self._animation)

            # Calculate a new position based on the current direction.
            self.rect = self._calc_new_position()

            if self._area.contains(self.rect):
                sprites_collided = pygame.sprite.spritecollide(
                    self, [sprite for sprite in self._collidable_sprites if
                           sprite.visible], None)

                if sprites_collided:
                    self._handle_collision(sprites_collided)
                elif not self._duration:
                    # The duration of the previous direction of movement
                    # has elapsed, so calculate a new direction with a new
                    # duration.
                    self._direction = self._calc_direction()
                    self._duration = self._update_count + random.choice(
                        range(MIN_DURATION, MAX_DURATION))
                elif self._update_count >= self._duration:
                    # We've reached the maximum duration in the given
                    # direction, so reset in order for the direction to be
                    # modified next cycle.
                    self._duration = 0
            else:
                # We've dropped off the bottom of the screen.
                self._on_destroyed(self)

        self._update_count += 1

    def _explode(self):
        """Run the explosion animation."""
        try:
            if self._update_count % 2 == 0:
                rect = self.rect
                self.image, self.rect = next(self._explode_animation)
                self.rect.center = rect.center
        except StopIteration:
            self._explode_animation = None
            self._on_destroyed(self)

    def _calc_new_position(self):
        offset_x = SPEED * math.cos(self._direction)
        offset_y = SPEED * math.sin(self._direction)

        return self.rect.move(offset_x, offset_y)

    def _handle_collision(self, sprites_collided):
        rects = [sprite.rect for sprite in sprites_collided]
        left, right, top, bottom = False, False, False, False

        for rect in rects:
            # Work out which of our sides are in contact.
            left = (left or rect.collidepoint(
                self.rect.topleft) or rect.collidepoint(
                self.rect.midleft) or rect.collidepoint(
                self.rect.bottomleft))

            right = (right or rect.collidepoint(
                self.rect.topright) or rect.collidepoint(
                self.rect.midright) or rect.collidepoint(
                self.rect.bottomright))

            top = (top or rect.collidepoint(
                self.rect.topleft) or rect.collidepoint(
                self.rect.midtop) or rect.collidepoint(
                self.rect.topright))

            bottom = (bottom or rect.collidepoint(
                self.rect.bottomleft) or rect.collidepoint(
                self.rect.midbottom) or rect.collidepoint(
                self.rect.bottomright))

        # Work out the new direction based on what we've collided with.
        self._direction = self._calc_direction(left, right, top, bottom)

    def _calc_direction(self, *args):
        """Calculate the direction of travel.

        Unless the sprite has collided (indicated by passing 4 booleans
        to this method), the direction of travel will tend towards the
        paddle.

        Args:
            args:
                Pass 4 booleans here to indicate which (if any) sides of the
                sprite are in collision (True for collision). This will
                affect the calculated direction.

        Returns:
            The direction in radians.
        """
        direction = self._direction

        if args:
            left, right, top, bottom = args
            # Calculate the direction based on any collision.
            if left and right and top:
                direction = HALF_PI
            elif left and right and bottom:
                direction = math.pi + HALF_PI
            elif left:
                direction = 0
            elif right:
                direction = math.pi

            direction += random.uniform(-0.05, 0.05)
        else:
            # No collision, so calculate the direction towards the paddle
            # but with some randomness applied.
            paddle_x, paddle_y = self._paddle.rect.center
            direction = math.atan2(paddle_y - self.rect.y,
                                   paddle_x - self.rect.x)

            direction += random.uniform(-RANDOM_RANGE, RANDOM_RANGE)

        return direction

    def explode(self):
        """Trigger an explosion of the enemy sprite."""
        self._explode_animation = iter(load_png_sequence('enemy_explosion'))
