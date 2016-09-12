import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round4 import Round4
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExtraLifePowerUp)


class Round3(BaseRound):
    """Initialises the background, brick layout and powerups for round 3."""

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
        self.next_round = Round4
        self.enemy_type = EnemyType.molecule
        self.num_enemies = 3

        # Reduce the speed of the ball slightly for this round, due to
        # the proximity of the bricks to the paddle.
        self.ball_base_speed_adjust = -2

        # Reduce the speed of the paddle slightly to help with precision
        # when controlling the ball in the confined starting space.
        self.paddle_speed_adjust = -2

        # Bring the ball back to base speed more quickly, otherwise it just
        # gets too hard to control in this level.
        self.ball_speed_normalisation_rate_adjust = 0.05

    def can_release_enemies(self):
        """Release the enemies right at the start."""
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_bricks(self):
        """Create the bricks and position them on the screen.

        Returns:
            A pygame.sprite.Group of bricks.
        """

        rows = []
        # Row 1
        rows += [BrickColour.green] * 13
        # Row 2
        rows += [BrickColour.white] * 3
        rows += [BrickColour.gold] * 10
        # Row 3
        rows += [BrickColour.red] * 5
        rows += [(BrickColour.red, DuplicatePowerUp)]
        rows += [BrickColour.red] * 7
        # Row 4
        rows += [BrickColour.gold] * 10
        rows += [BrickColour.white] * 3
        # Row 5
        rows += [BrickColour.pink] * 4
        rows += [(BrickColour.pink, DuplicatePowerUp)]
        rows += [BrickColour.pink] * 3
        rows += [(BrickColour.pink, ExtraLifePowerUp)]
        rows += [BrickColour.pink] * 4
        # Row 6
        rows += [BrickColour.blue] * 3
        rows += [BrickColour.gold] * 10
        # Row 7
        rows += [BrickColour.cyan] * 2
        rows += [(BrickColour.cyan,  CatchPowerUp)]
        rows += [BrickColour.cyan] * 3
        rows += [(BrickColour.cyan,  ExtraLifePowerUp)]
        rows += [BrickColour.cyan] * 6
        # Row 8
        rows += [BrickColour.gold] * 10
        rows += [(BrickColour.cyan,  CatchPowerUp)]
        rows += [BrickColour.cyan] * 2

        bricks = []
        x, y = 0, self._TOP_ROW_START

        for i, row in enumerate(rows):
            if i and i % 13 == 0:
                # New row
                y += 2
                x = 0
            try:
                colour, powerup = row
            except TypeError:
                colour, powerup = row, None
            brick = Brick(colour, 3, powerup_cls=powerup)
            bricks.append(self._blit_brick(brick, x, y))
            x += 1

        return pygame.sprite.Group(*bricks)

