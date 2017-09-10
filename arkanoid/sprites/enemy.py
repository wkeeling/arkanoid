import enum
import itertools
import logging
import math
import random
import weakref

import pygame

from arkanoid.utils.util import load_png_sequence

LOG = logging.getLogger(__name__)

# The speed the enemy sprite moves in pixels/frame.
SPEED = 2

# The enemy sprite is started in a downwards direction.
START_DIRECTION = 1.57  # Radians
# The enemy sprite travels in the start direction for this duration.
START_DURATION = 75  # Frames

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

    """Enumeration of enemy types to their image sequence prefix.
    """

    cube = 'enemy_cube'
    cone = 'enemy_cone'
    molecule = 'enemy_molecule'
    pyramid = 'enemy_pyramid'
    sphere = 'enemy_sphere'


class Enemy(pygame.sprite.Sprite):
    """An enemy is released from the doors in the top edge and slowly travels
    downwards towards the paddle.

    Its objective is to act as an obstruction and distraction. Enemies will
    increase the game score when destroyed.

    It is destroyed when hit by the ball, by a laser bullet or by the paddle.
    """

    # Enemies know about each other so they can collide with each other.
    _enemies = weakref.WeakSet()

    def __init__(self, enemy_type, paddle, on_paddle_collide,
                 collidable_sprites, on_destroyed):
        """
        Initialise a new enemy sprite.

        Args:
            enemy_type:
                The type of enemy which determines its appearance.
            paddle:
                The paddle instance.
            on_paddle_collide:
                Callback invoked when the enemy collides with the paddle. It
                takes 2 arguments: the enemy and the paddle.
            collidable_sprites:
                A list of sprites that can collide with the enemy. These
                sprites do not destroy the enemy, but cause the enemy to
                change direction.
            on_destroyed:
                Callback invoked when the enemy is destroyed, either by
                another sprite or when it falls off the bottom of the screen.
                It takes a single argument: the enemy sprite that's been
                destroyed.
        """
        super().__init__()
        self._enemies.add(self)
        self._paddle = paddle
        self._on_paddle_collide = on_paddle_collide
        self._on_destroyed = on_destroyed
        self._on_destroyed_called = False

        # Define the area within which the sprite will move.
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()

        # Set up the sequence of images that will animate the enemy sprite.
        self._animation, width, height = self._load_animation_sequence(
            enemy_type.value)

        # Set up the rect that defines the starting position of the sprite,
        # and which also defines its dimensions - which must be big enough
        # to fit the largest of the frames in the animation.
        self.rect = pygame.Rect(self._area.center, (width, height))
        self.image = None

        # The exploding animation when we've been struck by the ball or paddle.
        self._explode_animation = None

        # The sprites in the game that cause the enemy sprite to change
        # direction when it collides with them.
        self._collidable_sprites = pygame.sprite.Group()
        for sprite in collidable_sprites:
            self._collidable_sprites.add(sprite)

        # The current direction of travel of the sprite.
        self._direction = START_DIRECTION

        # The duration which the sprite will travel in a set direction.
        # This is an update count value. When the update count reaches this
        # value, the direction will be recalculated.
        self._duration = START_DURATION

        # The enemy sprite is in contact mode after it collides with another
        # sprite that causes it to change direction (rather than destroy it).
        # It remains in contact mode for a number of cycles after the last
        # collision. This attribute tracks the last cycle a contact was made.
        self._last_contact = 0

        # Stops the enemy sprite from moving if set to True.
        self.freeze = False

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

            if not self.freeze:
                # Calculate a new position based on the current direction.
                self.rect = self._calc_new_position()

                if self._area.contains(self.rect):
                    if pygame.sprite.spritecollide(self, [self._paddle],
                                                   False):
                        self._on_paddle_collide(self, self._paddle)
                    else:
                        visible_sprites = itertools.chain(
                            (sprite for sprite in self._collidable_sprites if
                             sprite.visible),
                            (sprite for sprite in self._enemies if
                             sprite.visible and sprite is not self)
                        )
                        sprites_collided = pygame.sprite.spritecollide(
                            self,
                            visible_sprites, None)

                        # The following code could be pulled into a separate
                        # strategy class which could be passed to the enemy
                        # when it is initialised. This could act as the default
                        # movement behaviour, and would allow rounds to
                        # inject their own strategy classes when they wanted
                        # their own round specific movement behaviour.
                        #####################################################

                        if sprites_collided:
                            self._last_contact = self._update_count
                            self._direction = self._calc_direction_collision(
                                sprites_collided)
                        elif self._update_count > self._last_contact + 30:
                            # Last contact not made for past 30 updates, so
                            # recalculate direction using free movement
                            # algorithm.
                            if not self._duration:
                                # The duration of the previous direction of
                                # free movement has elapsed, so calculate a new
                                # direction with a new duration.
                                self._direction = self._calc_direction()
                                self._duration = (
                                    self._update_count + random.choice(
                                        range(MIN_DURATION, MAX_DURATION)))
                            elif self._update_count >= self._duration:
                                # We've reached the maximum duration in the
                                # given direction, so reset in order for the
                                # direction to be modified next cycle.
                                self._duration = 0

                        #####################################################
                else:
                    # We've dropped off the bottom of the screen.
                    if not self._on_destroyed_called:
                        self._on_destroyed(self)
                        self._on_destroyed_called = True

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

    def _calc_direction_collision(self, sprites_collided):
        """Calculate a new direction based upon the sprites we collided with.

        Args:
            sprites_collided:
                A list of sprites that we have collided with.
        Returns:
            The direction in radians.
        """
        # Map out the sides of the object, excluding the corners. Here we use
        # 5 pixel wide rectangles to represent each side.
        top = pygame.Rect(self.rect.left + 5, self.rect.top,
                          self.rect.width - 10, 5)
        left = pygame.Rect(self.rect.left, self.rect.top + 5, 5,
                           self.rect.height - 10)
        bottom = pygame.Rect(self.rect.left + 5, self.rect.top +
                             self.rect.height - 5, self.rect.width - 10, 5)
        right = pygame.Rect(self.rect.left + self.rect.width - 5,
                            self.rect.top + 5, 5, self.rect.height - 10)

        rects = [sprite.rect for sprite in sprites_collided]
        cleft, cright, ctop, cbottom = False, False, False, False

        for rect in rects:
            # Work out which of our sides are in contact.
            cleft = cleft or left.colliderect(rect)
            cright = cright or right.colliderect(rect)
            ctop = ctop or top.colliderect(rect)
            cbottom = cbottom or bottom.colliderect(rect)

        direction = self._direction

        # Work out the new direction based on what we've collided with.
        if cleft and cright and ctop and cbottom:
            # When all 4 sides collide, try to send back in direction
            # from which originated. Should probably freeze instead.
            direction = -direction
        elif cleft and cright and cbottom:
            direction = math.pi + HALF_PI
        elif cleft and cright and ctop:
            direction = HALF_PI
        elif cleft and cbottom:
            direction = 0
        elif cright and cbottom:
            direction = math.pi
        elif cbottom:
            if direction not in (0, math.pi):
                direction = 0
        else:
            # Any other combination causes a downward direction. This may
            # include a corner collision - as we don't detect those.
            direction = math.pi - HALF_PI
            if cleft or cright:
                # Prevent the sprite from getting 'stuck' to walls.
                if self._update_count % 60 == 0:
                    if cright:
                        direction = math.pi
                    else:
                        direction = 0

        return direction

    def _calc_direction(self):
        """Calculate the direction of travel when the sprite is moving
        freely (has not collided).

        When moving freely (not colliding) the enemy sprites will gradually
        move towards the paddle.

        Returns:
            The direction in radians.
        """
        # No collision, so calculate the direction towards the paddle
        # but with some randomness applied.
        paddle_x, paddle_y = self._paddle.rect.center
        direction = math.atan2(paddle_y - self.rect.y,
                               paddle_x - self.rect.x)

        direction += random.uniform(-RANDOM_RANGE, RANDOM_RANGE)

        return direction

    def explode(self):
        """Trigger an explosion of the enemy sprite."""
        if not self._explode_animation:
            self._explode_animation = iter(
                load_png_sequence('enemy_explosion'))

    def reset(self):
        """Reset the enemy state back to its starting state."""
        self._direction = START_DIRECTION
        self._duration = START_DURATION
        self._on_destroyed_called = False
        self.visible = True
        self.freeze = False
