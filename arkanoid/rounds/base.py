import collections

import pygame

from arkanoid.sprites.edge import (TopEdge,
                                   SideEdge)
from arkanoid.sprites.brick import BrickColour

# The default base speed. This is the starting speed of the ball, and the
# speed that the ball will slowly try to arrive at if it has been sped up or
# slowed down down by something.
BALL_BASE_SPEED = 9  # pixels per frame

# The default speed adjustment that is applied to the ball when it collides
# with a brick.
BRICK_SPEED_ADJUST = 0.5

# RGB sequences for background colours.
BLUE = (0, 0, 128)
GREEN = (0, 128, 0)
RED = (128, 0, 0)


class BaseRound:
    """Abstract base class for all Arkanoid rounds.

    Subclasses must implement the abstract hook methods defined here.
    """

    def __init__(self, top_offset):
        """Initialise the BaseRound.

        Args:
            top_offset:
                The number of pixels from the top of the screen before the
                top edge can be displayed.
        """
        self.top_offset = top_offset
        self.screen = pygame.display.get_surface()

        # The name of the round displayed on the screen when the round starts.
        self.name = 'Round name not set!'

        # The edges used as the sides of the game area.
        # A named tuple referencing the 3 game edge sprites with the
        # attributes: 'left', 'right', 'top'.
        self.edges = self._create_edges()

        # The background for this round.
        self.background = self._create_background()

        # Background (plus edges) are blitted to the screen.
        self.screen.blit(self.background, (0, top_offset))

        # Create the bricks that the ball can collide with, positioning
        # them on the screen.
        self.bricks = self._create_bricks()

        # The base speed of the ball for the round.
        self.ball_base_speed = BALL_BASE_SPEED

        # The adjustment in ball speed caused by colliding with a brick.
        # Some rounds may need to modify this if their bricks are spaced
        # close together, to prevent the ball from getting too fast.
        self.brick_speed_adjust = BRICK_SPEED_ADJUST

        # Per-frame rate at which ball is brought back to base speed.
        self.ball_speed_normalisation_rate = 0.02

        # The class of the enemy to release in this round. Subclasses to
        # override with the specific class.
        self.enemy_type = None

        # The number of enemies to release. Subclasses to override with a
        # specific number.
        self.num_enemies = 0

        # Reference to the next round, to be overriden by subclasses.
        self.next_round = None

        # Keep track of the number of destroyed bricks.
        self._bricks_destroyed = 0

    @property
    def complete(self):
        """Whether the rounds has been completed (all bricks destroyed).
        
        Returns:
            True if the round has been completed. False otherwise.
        """
        return self._bricks_destroyed >= len([brick for brick in self.bricks
                                              if brick.colour !=
                                              BrickColour.gold])

    def brick_destroyed(self):
        """Conveys to the round that a brick has been destroyed in the game."""
        self._bricks_destroyed += 1

    def can_release_enemies(self):
        """Whether the enemies can be released into the game.

        This is round specific, so concrete round subclasses should implement
        this method.
        """
        raise NotImplementedError('Subclasses must implement '
                                  'can_release_enemies()')

    def _blit_brick(self, brick, x, y):
        """Blits the specified brick onto the game area by using a
        relative coordinate for the position of the brick.

        This is a convenience method that concrete round subclasses can use
        when setting up bricks. It assumes that the game area (area within
        the edges) is split into a grid where each grid square corresponds to
        one brick. The top left most brick is considered position (0, 0).

        This allows clients to avoid having to work with actual screen
        positions.

        Note that this method will modify the brick's rect attribute once
        the brick has been set.

        Args:
            brick:
                The brick instance to position on the grid.
            x:
                The x position on the grid.
            y:
                The y position on the grid.
        Returns:
            The blitted brick.
        """
        offset_x = brick.rect.width * x
        offset_y = brick.rect.height * y

        rect = self.screen.blit(brick.image, (self.edges.left.rect.x +
                                self.edges.left.rect.width + offset_x,
                                self.edges.top.rect.y +
                                self.edges.top.rect.height + offset_y))
        brick.rect = rect
        return brick

    def _create_background(self):
        """Create the background surface for the round.

        Subclasses must override this abstract method to return the
        background surface.

        Returns:
            The background surface.
        """
        raise NotImplementedError(
            'Subclasses must implement _create_background()')

    def _create_edges(self):
        """Create the edge sprites and position them at the edges of the
        screen.

        This implementation creates static edges. Subclasses may override
        if they wish to provide some special animation within an edge.

        Returns:
            A named tuple with attributes 'left', 'right', and 'top' that
            reference the corresponding edge sprites.
        """
        edges = collections.namedtuple('edge', 'left right top')
        left_edge = SideEdge('left')
        right_edge = SideEdge('right')
        top_edge = TopEdge()
        left_edge.rect.topleft = 0, self.top_offset
        right_edge.rect.topright = self.screen.get_width(), self.top_offset
        top_edge.rect.topleft = left_edge.rect.width, self.top_offset
        return edges(left_edge, right_edge, top_edge)

    def _create_bricks(self):
        """Create the bricks and position them on the screen.

        Subclasses must override this abstract method to create and position
        the bricks.

        Returns:
            A pygame.sprite.Group of bricks.
        """
        raise NotImplementedError('Subclasses must implement _create_bricks()')

