import itertools

import pygame

from arkanoid.rounds.base import BaseRound


class Round1(BaseRound):
    """Initialises the background, brick layout and powerups for round two."""

    # The offset from the top edge to where the bottom row of bricks starts.
    _BOTTOM_ROW_VERTICAL_OFFSET = 500

    def __init__(self, top_offset):
        """Initialise round 2.

        Args:
            top_offset:
                The number of pixels from the top of the screen before the
                top edge can be displayed.
        """
        super().__init__(top_offset)

        self.name = 'Round 2'

    def _create_background(self):
        background = pygame.Surface(self.screen.get_size())
        background = background.convert()
        # TODO: background image should be loaded from a file.
        background.fill((0, 128, 0))
        return background

    def _create_bricks(self):
        """Create the bricks and position them on the screen.

        Returns:
            A pygame.sprite.Group of bricks.
        """
        colours = itertools.cycle(('white', 'amber', 'cyan', 'green', 'red',
                                  'blue', 'magenta', 'yellow'))


        for i in reversed(range(13)):
            pass

