import collections

import pygame

from arkanoid.utils import load_png


class Round1:
    """Initialises the background, brick layout and powerups for round one.
    TODO: define the attributes that make a round (e.g. background, edges
    named tuple, etc.)
    """

    # How far down the screen the bottom row of bricks starts
    _BOTTOM_ROW_START = 200

    def __init__(self):
        screen = pygame.display.get_surface()

        # The round specific background.
        self.background = self._initialise_background(screen)

        # These edges have been blitted to the background and are used
        # as the sides of the game area.
        self.edges = self._initialise_edges()

        # Background (plus edges) are blitted to the screen.
        screen.blit(self.background, (0, 0))

        # Create the Bricks that the ball can collide with.
        self.bricks = self._initialise_bricks(screen)

        # The caption of the round, displayed on screen.
        self.caption = 'Round 1'

        # The class of the next round after this.
        self.next_round = None

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

    def _initialise_background(self, screen):
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        # TODO: background image should be loaded from a file.
        background.fill((0, 0, 0))
        return background

    def _initialise_edges(self):
        # The edges are blitted to the background.
        edges = collections.namedtuple('edge', 'left right top')
        side_edge, _ = load_png('edge.png')
        top_edge, _ = load_png('top.png')
        left_rect = self.background.blit(side_edge, (0, 0))
        right_rect = self.background.blit(side_edge, (
            self.background.get_rect().width - side_edge.get_width(), 0))
        top_rect = self.background.blit(top_edge, (side_edge.get_width(), 0))
        return edges(left_rect, right_rect, top_rect)

    def _initialise_bricks(self, screen):
        # TODO bricks should be sprites.Brick that have rect and powerup attrs
        bricks = []
        colours = 'green', 'blue', 'yellow', 'red', 'grey'
        top = self._BOTTOM_ROW_START

        for colour in colours:
            # Each coloured brick forms a new layer.
            brick, rect = load_png('brick_{}.png'.format(colour))
            left = self.edges[0].width
            for i in range(13):
                # Each layer consists of 13 bricks added horizontally.
                rect = screen.blit(brick, (left, top))
                left += rect.width+1
                bricks.append(rect)
            top -= rect.height

        return bricks


    # TODO: when initialised, blits the background to the screen and exposes
    # it as a background attribute. Blits the bricks to the screen and exposes
    # them as a bricks attribute. This is a list of Brick objects. Each one
    # has a rect attribute and a powerup attribute - which may be None.
    # A Brick object
    # has a powerup attribute which references the CLASS of the powerup. All
    # powerup classes take the Game instance as an argument to their initialiser
    # and thus have access to the ball, paddle, lives as necessary.
        # The game should powerup.deactivate() existing powerup
        # before initialising new one.