import pygame


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

        # The background for this round.
        self.background = self._create_background()

        # The edges used as the sides of the game area.
        # A named tuple referencing the 3 game edge sprites with the
        # attributes: 'left', 'right', 'top'.
        self.edges = self._create_edges()

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

        Subclasses must override this abstract method to create and position
        the edge sprites.

        Returns:
            A named tuple with attributes 'left', 'right', and 'top' that
            reference the corresponding edge sprites.
        """
        raise NotImplementedError('Subclasses must implement _create_edges()')

    def _create_bricks(self):
        """Create the bricks and position them on the screen.

        Subclasses must override this abstract method to create and position
        the bricks.

        Returns:
            A pygame.sprite.Group of bricks.
        """
        raise NotImplementedError('Subclasses must implement _create_bricks()')
