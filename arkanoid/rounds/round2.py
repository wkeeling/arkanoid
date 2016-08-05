import itertools
import random

import pygame

from arkanoid.rounds.base import BaseRound
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


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
        background.fill((0, 128, 0))
        return background

    def _create_bricks(self):
        """Create the bricks and position them on the screen.

        Returns:
            A pygame.sprite.Group of bricks.
        """
        colours = itertools.cycle((BrickColour.white, BrickColour.orange,
                                   BrickColour.cyan, BrickColour.green,
                                   BrickColour.red,
                                   BrickColour.blue, BrickColour.pink,
                                   BrickColour.yellow))
        left = self.edges.left.rect.width
        bricks = []
        first_row_powerups = self._create_first_row_powerups()
        remaining_powerups = self._create_remaining_powerups()

        # Create a dict structure with the brick index as the key, and
        # powerup class as the value.
        first_row_powerup_indexes = dict(zip(random.sample(range(13),
                                             len(first_row_powerups)),
                                             first_row_powerups))
        remaining_powerup_indexes = dict(zip(random.sample(range(91),
                                             len(remaining_powerups)),
                                             remaining_powerups))

        count = 0
        for i in reversed(range(13)):
            # Create the first row brick.
            powerup = first_row_powerup_indexes.get(i)
            top = self._BOTTOM_ROW_VERTICAL_OFFSET
            if i > 0:
                brick = Brick(BrickColour.silver.name,
                              BrickColour.silver.value * 2, destroy_after=2,
                              powerup_cls=powerup)
            else:
                brick = Brick(BrickColour.red.name, BrickColour.red.value,
                              destroy_after=1,
                              powerup_cls=powerup)

            bricks.append(self._blit_brick(brick, left, top))

            colour = next(colours)
            for _ in range(i):
                # Create a vertical column of bricks above the first.
                powerup = remaining_powerup_indexes.get(count)
                top = top - brick.rect.height
                brick = Brick(colour.name, colour.value,
                              destroy_after=1, powerup_cls=powerup)
                bricks.append(self._blit_brick(brick, left, top))
                count += 1

            left += brick.rect.width+1

        return bricks

    def _create_first_row_powerups(self):
        # Create slow ball and catch for the first row, given the
        # lack of space beneath.
        first_row_powerups = []
        first_row_powerups.extend([SlowBallPowerUp] * 3)
        first_row_powerups.extend([CatchPowerUp] * 2)
        random.shuffle(first_row_powerups)
        return first_row_powerups

    def _create_remaining_powerups(self):
        remaining_powerups = []
        # Powerups for the other bricks
        remaining_powerups.extend([ExtraLifePowerUp] * 3)
        remaining_powerups.extend([LaserPowerUp] * 4)
        remaining_powerups.extend([CatchPowerUp] * 2)
        remaining_powerups.extend([ExpandPowerUp] * 4)
        remaining_powerups.extend([SlowBallPowerUp] * 2)
        remaining_powerups.extend([DuplicatePowerUp] * 2)
        random.shuffle(remaining_powerups)
        return remaining_powerups

    def _blit_brick(self, brick, left, top):
        rect = self.screen.blit(brick.image, (left, top))
        brick.rect = rect
        return brick
