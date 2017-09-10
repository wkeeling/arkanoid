import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


class Round5(BaseRound):
    """Initialises the background, brick layout and powerups for round 5."""

    _TOP_ROW_START = 5

    def __init__(self, top_offset):
        """Initialise round 5.

        Args:
            top_offset:
                The number of pixels from the top of the screen before the
                top edge can be displayed.
        """
        super().__init__(top_offset)

        self.name = 'Round 5'
        self.enemy_type = EnemyType.cone
        self.num_enemies = 3

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
        bricks = [self._blit_brick(Brick(BrickColour.orange, 5,
                                         powerup_cls=ExpandPowerUp), 4, 2),
                  self._blit_brick(Brick(BrickColour.orange, 5,
                                         powerup_cls=LaserPowerUp), 8, 2),
                  self._blit_brick(Brick(BrickColour.orange, 5), 5, 3),
                  self._blit_brick(Brick(BrickColour.orange, 5,
                                         powerup_cls=SlowBallPowerUp), 7, 3),
                  self._blit_brick(Brick(BrickColour.orange, 5), 5, 4),
                  self._blit_brick(Brick(BrickColour.orange, 5), 7, 4)]

        for y in range(5, 7):
            for x in range(4, 9):
                bricks.append(self._blit_brick(Brick(BrickColour.silver, 5),
                                               x, y))

        for y in range(7, 9):
            for x in range(3, 10):
                colour = BrickColour.silver
                powerup_cls = None
                if x in (5, 7):
                    colour = BrickColour.red
                    if (x, y) == (5, 8):
                        powerup_cls = CatchPowerUp
                    elif (x, y) == (7, 8):
                        powerup_cls = DuplicatePowerUp
                bricks.append(self._blit_brick(
                    Brick(colour, 5, powerup_cls=powerup_cls), x, y))

        for y in range(9, 16):
            for x in range(2, 11):
                if (x, y) not in [(3, 11), (9, 11), (3, 12), (5, 12),
                                  (6, 12), (7, 12), (9, 12), (3, 13),
                                  (5, 13), (6, 13), (7, 13), (9, 13),
                                  (2, 14), (3, 14), (4, 14), (6, 14),
                                  (8, 14), (9, 14), (10, 14), (2, 15),
                                  (3, 15), (4, 15), (6, 15), (8, 15),
                                  (9, 15), (10, 15)]:
                    powerup_cls = None
                    if (x, y) == (7, 14):
                        powerup_cls = LaserPowerUp
                    bricks.append(self._blit_brick(
                        Brick(BrickColour.silver, 5,
                              powerup_cls=powerup_cls), x, y))

        return pygame.sprite.Group(*bricks)

