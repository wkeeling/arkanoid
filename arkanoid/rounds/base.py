import collections

import pygame

from arkanoid.sprites.edge import (TopEdge,
                                   SideEdge)


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

        # The name of the round displayed on the screen when the round starts.
        self.name = 'Round name not set!'

        # Keep track of the number of destroyed bricks.
        self._bricks_destroyed = 0

    @property
    def complete(self):
        """Whether the rounds has been completed (all bricks destroyed).
        
        Returns:
            True if the round has been completed. False otherwise.
        """
        return self._bricks_destroyed == len(self.bricks)

    def brick_destroyed(self):
        """Conveys to the Round that a brick has been destroyed in the game."""
        self._bricks_destroyed += 1

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
