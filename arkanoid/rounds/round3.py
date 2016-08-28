import random

import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


class Round3(BaseRound):
    """Initialises the background, brick layout and powerups for round 3.
    """

    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        """Initialise round 3.

        Args:
            top_offset:
                The number of pixels from the top of the screen before the
                top edge can be displayed.
        """
        super().__init__(top_offset)

        self.name = 'Round 3'
        self.enemy_type = EnemyType.molecule
        self.num_enemies = 3

    def can_release_enemies(self):
        """Release the enemies right at the start."""
        return True

    def _create_background(self):
        background = pygame.Surface(self.screen.get_size())
        background = background.convert()
        background.fill(BLUE)
        return background

    def _create_bricks(self):
        """Create the bricks and position them on the screen.

        Returns:
            A pygame.sprite.Group of bricks.
        """
        rows = (BrickColour.green,
                (BrickColour.white, BrickColour.gold),
                BrickColour.red,
                (BrickColour.gold, BrickColour.white),
                BrickColour.pink,
                (BrickColour.blue, BrickColour.gold),
                BrickColour.cyan,
                (BrickColour.gold, BrickColour.cyan))

        bricks = []
        y = self._TOP_ROW_START

        for i, row in enumerate(rows):
            if i % 2 == 0:
                for x in range(13):
                    if row == BrickColour.cyan and x == 4:
                        powerup = ExtraLifePowerUp
                    else:
                        powerup = None
                    brick = Brick(row, 3, powerup_cls=powerup)
                    bricks.append(self._blit_brick(brick, x, y))
            else:
                start = 0
                for colour in row:
                    if colour == BrickColour.gold:
                        for j in range(10):
                            brick = Brick(colour, 3)
                            bricks.append(
                                self._blit_brick(brick, start + j, y))
                        start = 10
                    else:
                        for j in range(3):
                            if colour == BrickColour.cyan and j == 0:
                                powerup = CatchPowerUp
                            elif colour == BrickColour.blue and j == 1:
                                powerup = DuplicatePowerUp
                            else:
                                powerup = None
                            brick = Brick(colour, 3, powerup_cls=powerup)
                            bricks.append(
                                self._blit_brick(brick, start + j, y))
                        start = 3
            y += 2

        return pygame.sprite.Group(*bricks)

