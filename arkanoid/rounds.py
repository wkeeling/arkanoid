import pygame

from arkanoid.utils import load_png


class RoundOne:
    """Initialises the background, brick layout and powerups for round one."""

    # How far down the screen the bottom row of bricks starts
    _BOTTOM_ROW_START = 200

    def __init__(self, screen):
        self.background = self._initialise_background(screen)
        self.edges = self._initialise_edges(screen)
        # Background (plus edges) are blitted to the screen.
        screen.blit(self.background, (0, 0))
        self.bricks = self._initialise_bricks(screen)
        self.caption = 'Round One'
        self.next_round = None

    def _initialise_background(self, screen):
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        # TODO: background image should be loaded from a file.
        background.fill((0, 0, 0))
        return background

    def _initialise_edges(self, screen):
        # The edges are loaded and then blitted to the background.
        edge, _ = load_png('edge.png')
        left_rect = self.background.blit(edge, (0, 0))
        right_rect = self.background.blit(edge, (
            screen.get_rect().width - edge.get_width(), 0))
        top_edge, _ = load_png('top.png')
        top_rect = self.background.blit(top_edge, (edge.get_width(), 0))
        return left_rect, right_rect, top_rect

    def _initialise_bricks(self, screen):
        # TODO bricks should be sprites.Brick that have rect and powerup attrs
        bricks = []
        colours = 'green', 'blue', 'yellow', 'red', 'grey'
        top = self._BOTTOM_ROW_START

        for colour in colours:
            # Each coloured brick forms a new layer.
            brick, rect = load_png('brick_{}.png'.format(colour))
            left = self.edges[0]
            for i in range(13):
                # Each layer consists of 13 bricks added horizontally.
                rect = screen.blit(brick, (left, top))
                left += rect.width
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