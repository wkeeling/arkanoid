import collections
import random

import pygame

from arkanoid.sprites.brick import Brick
from arkanoid.sprites.edge import (TopEdge,
                                   SideEdge)
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)
from arkanoid.util import load_png


class Round1:
    """Initialises the background, brick layout and powerups for round one."""

    _POWERUP_CLASSES = (CatchPowerUp, ExpandPowerUp, ExtraLifePowerUp,
                        SlowBallPowerUp, LaserPowerUp)

    # How far down the screen the bottom row of bricks starts
    _BOTTOM_ROW_START = 200

    def __init__(self):
        self._screen = pygame.display.get_surface()

        # The background for this round.
        self.background = self._create_background()

        # The edges used as the sides of the game area.
        self.edges = self._create_edges()

        # Background (plus edges) are blitted to the screen.
        self._screen.blit(self.background, (0, 0))

        # Create the Bricks that the ball can collide with.
        self.bricks = self._create_bricks()

        # Position the bricks on the screen.
        self._position_bricks(self._screen)

        # The caption of the round, displayed on screen.
        self.caption = 'Round 1'

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
        background = pygame.Surface(self._screen.get_size())
        background = background.convert()
        # TODO: background image should be loaded from a file.
        background.fill((0, 0, 0))
        return background

    def _create_edges(self):
        edges = collections.namedtuple('edge', 'left right top')
        left_edge = SideEdge()
        right_edge = SideEdge()
        top_edge = TopEdge()
        left_edge.rect.topleft = 0, 0
        right_edge.rect.topright = self._screen.get_width(), 0
        top_edge.rect.topleft = left_edge.rect.width, 0
        return edges(left_edge, right_edge, top_edge)

    def _create_bricks(self):
        bricks = []
        colours = 'green', 'blue', 'yellow', 'red', 'grey'

        # Create the distribution of powerup classes.
        powerup_classes = []
        powerup_classes.extend([CatchPowerUp] * 2)
        powerup_classes.extend([ExpandPowerUp] * 3)
        powerup_classes.extend([ExtraLifePowerUp] * 2)
        powerup_classes.extend([SlowBallPowerUp] * 2)
        powerup_classes.extend([LaserPowerUp] * 3)
        random.shuffle(powerup_classes)

        # Randomly select the indexes for the bricks that will contain
        # powerups.
        powerup_indexes = random.sample(range(65), len(powerup_classes))

        # Count the bricks created.
        count = 0

        # Each coloured brick forms a new layer.
        for colour in colours:
            # Grey bricks take 2 hits to destroy.
            destroy_after = 2 if colour == 'grey' else 1

            for i in range(13):
                powerup_class = None

                if count in powerup_indexes:
                    powerup_class = powerup_classes.pop(0)

                brick = Brick(colour, destroy_after=destroy_after,
                              powerup_cls=powerup_class)

                bricks.append(brick)
                count += 1

        return bricks

    def _position_bricks(self, background):
        top = self._BOTTOM_ROW_START
        colour, rect = None, None

        for brick in self.bricks:
            if colour != brick.colour:
                colour = brick.colour
                left = self.edges.left.rect.width
                if rect:
                    top -= rect.height

            if brick.visible:
                # Each layer consists of 13 bricks added horizontally.
                rect = background.blit(brick.image, (left, top))
                # Update the brick's rect with the new position
                brick.rect = rect

            left += rect.width+1
