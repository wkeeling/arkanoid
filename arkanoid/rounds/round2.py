import itertools

import pygame

from arkanoid.rounds.base import BaseRound
from arkanoid.sprites.brick import Brick


class Round2(BaseRound):
    """Initialises the background, brick layout and powerups for round two."""

    # The offset from the top edge to where the bottom row of bricks starts.
    _BOTTOM_ROW_VERTICAL_OFFSET = 475

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
        left = self.edges.left.rect.width
        bricks = []

        for i in reversed(range(13)):
            top = self._BOTTOM_ROW_VERTICAL_OFFSET
            if i > 0:
                brick = Brick('grey', 80, destroy_after=2, powerup_cls=None)
            else:
                brick = Brick('red', 80, destroy_after=1, powerup_cls=None)

            bricks.append(self._blit_brick(brick, left, top))

            colour = next(colours)
            for _ in range(i):
                top = top - brick.rect.height
                brick = Brick(colour, 80 + ((i + 1) * 10),
                              destroy_after=1, powerup_cls=None)
                bricks.append(self._blit_brick(brick, left, top))

            left += brick.rect.width+1

        return bricks

    def _blit_brick(self, brick, left, top):
        rect = self.screen.blit(brick.image, (left, top))
        brick.rect = rect
        return brick
