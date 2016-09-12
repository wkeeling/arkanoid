import itertools
import random

import pygame

from arkanoid.rounds.base import (BaseRound,
                                  GREEN)
from arkanoid.rounds.round3 import Round3
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


class Round2(BaseRound):
    """Initialises the background, brick layout and powerups for round 2."""

    _BRICK_START_ROW = 16

    def __init__(self, top_offset):
        """Initialise round 2.

        Args:
            top_offset:
                The number of pixels from the top of the screen before the
                top edge can be displayed.
        """
        super().__init__(top_offset)

        self.name = 'Round 2'
        self.next_round = Round3
        self.enemy_type = EnemyType.pyramid
        self.num_enemies = 3

    def can_release_enemies(self):
        """Release the enemies right at the start."""
        return True

    def _get_background_colour(self):
        return GREEN

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

        x, count = 0, 0
        for i in reversed(range(13)):
            # Create the first row brick.
            powerup = first_row_powerup_indexes.get(i)
            y = self._BRICK_START_ROW
            if i > 0:
                brick = Brick(BrickColour.silver, 2, powerup_cls=powerup)
            else:
                brick = Brick(BrickColour.red, 2, powerup_cls=SlowBallPowerUp)

            bricks.append(self._blit_brick(brick, x, y))

            colour = next(colours)
            for _ in range(i):
                # Create a vertical column of bricks above the first.
                powerup = remaining_powerup_indexes.get(count)
                y -= 1
                brick = Brick(colour, 2, powerup_cls=powerup)
                bricks.append(self._blit_brick(brick, x, y))
                count += 1

            x += 1

        return pygame.sprite.Group(*bricks)

    def _create_first_row_powerups(self):
        # Create slow ball and catch for the first row, given the
        # lack of space beneath.
        first_row_powerups = []
        first_row_powerups.extend([SlowBallPowerUp] * 2)
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
