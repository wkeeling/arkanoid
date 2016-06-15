import collections
import logging
import sys

import pygame

from arkanoid.rounds import RoundOne
from arkanoid.sprites import Ball
from arkanoid.sprites import Paddle
from arkanoid.utils import load_png

LOG = logging.getLogger(__name__)

# The speed the game runs at in FPS.
GAME_SPEED = 60
# The dimensions of the main game window in pixels.
DISPLAY_SIZE = 600, 650
# The title of the main window.
DISPLAY_CAPTION = 'Arkanoid'
# The angle the ball initially moves off the paddle, in radians.
BALL_START_ANGLE_RAD = 5.0
# The speed that the ball will always try to arrive at.
BALL_BASE_SPEED = 8  # pixels per-frame
# The max speed of the ball, prevents a runaway speed when lots of rapid
# collisions.
BALL_MAX_SPEED = 15  # pixels per-frame
# Per-frame rate at which ball is brought back to base speed.
BALL_SPEED_NORMALISATION_RATE = 0.02
# Increase in speed caused by colliding with a brick.
BRICK_SPEED_ADJUST = 0.5
# Increase in speed caused by colliding with a wall.
WALL_SPEED_ADJUST = 0.2
# The speed the paddle moves.
PADDLE_SPEED = 10


class Arkanoid:

    def __init__(self):
        # Initialise the pygame modules.
        pygame.init()

        # Create the screen.
        self._screen = self._create_screen()

        # Initialise the clock.
        self._clock = pygame.time.Clock()

        # Reference to a running game, when one is in play
        self._game = None

    def main_loop(self):
        running = True

        while running:
            # Game runs at 60 fps.
            self._clock.tick(GAME_SPEED)

            # Monitor for key presses.
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    running = False

            #TODO: add logic to begin game
            if not self._game:
                self._game = Game(self._screen)

            if self._game:
                self._game.update(event_list)

            # Display all updates.
            pygame.display.flip()

        LOG.debug('Exiting')

    def _create_screen(self):
        screen = pygame.display.set_mode(DISPLAY_SIZE)
        pygame.display.set_caption(DISPLAY_CAPTION)
        pygame.mouse.set_visible(False)
        return screen


class Game:

    def __init__(self, screen, lives=3):
        self._screen = screen

        # Keep track of the score and lives throughout the game.
        self.score = 0
        self.lives = lives

        # The raw unblitted edges are loaded once and held by the game.
        self._edges = self._create_edges()

        # The current round.
        self._round = None

        # The sprites.
        self.paddle = Paddle(left_offset=self._edges.side.get_width(),
                             right_offset=self._edges.side.get_width(),
                             bottom_offset=50,
                             speed=PADDLE_SPEED)

        self.ball = Ball(start_pos=self.paddle.rect.midtop,
                         start_angle=BALL_START_ANGLE_RAD,
                         base_speed=BALL_BASE_SPEED,
                         max_speed=BALL_MAX_SPEED,
                         normalisation_rate=BALL_SPEED_NORMALISATION_RATE,
                         off_screen_callback=self._off_screen)

        # The current powerup, if any.
        self.active_powerup = None

        # Whether the game is finished.
        self.over = False

    def _create_edges(self):
        edges = collections.namedtuple('edges', 'side top')
        side_edge, _ = load_png('edge.png')
        top_edge, _ = load_png('top.png')
        return edges(side_edge, top_edge)

    def update(self, events):
        if not self._round or self._round.complete:
            self._new_round()

        self._handle_events(events)
        self._update_sprites()

    def _new_round(self):
        # Get the next round.
        if self._round is None:
            self._round = RoundOne(self._screen, self._edges)
        else:
            self._round = self._round.next_round

        # Re-populate the ball with the collidable objects it needs
        # to know about.
        self.ball.remove_all_collidable_objects()
        for edge in self._round.edges:
            # Every collision with a wall momentarily increases the speed
            # of the ball.
            self.ball.add_collidable_object(edge,
                                            speed_adjust=WALL_SPEED_ADJUST)
        self.ball.add_collidable_object(
            self.paddle,
            bounce_strategy=self.paddle.bounce_strategy)

        for brick in self._round.bricks:
            # Make the ball aware of the bricks it might collide with.
            # Every brick collision momentarily increases the speed of
            # the ball.
            self.ball.add_collidable_object(
                brick,
                speed_adjust=BRICK_SPEED_ADJUST,
                on_collide=self._on_brick_collide)

    def _handle_events(self, event_list):
        for event in event_list:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.paddle.move_left()
                elif event.key == pygame.K_RIGHT:
                    self.paddle.move_right()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    self.paddle.stop()

    def _update_sprites(self):
        # Erase the previous location of the sprites.
        self._screen.blit(self._round.background, self.paddle.rect,
                          self.paddle.rect)
        self._screen.blit(self._round.background, self.ball.rect,
                          self.ball.rect)

        # Update the state of the sprites and redraw them.
        self.paddle.update()
        self._screen.blit(self.paddle.image, self.paddle.rect)
        self.ball.update()
        self._screen.blit(self.ball.image, self.ball.rect)

    def _on_brick_collide(self, brick):
        # Tell the ball that the brick has gone.
        self.ball.remove_collidable_object(brick)

        # Tell the round that a brick has gone, so that it can decide
        # whether the round is completed.
        self._round.brick_destroyed()

        # Erase the brick from the screen.
        self._screen.blit(self._round.background, brick, brick)

        # TODO: we need to check the brick's powerup attribiute (once brick
        # becomes a real object). If it has a powerup, initialise the powerup
        # passing in the game instance (self). Also need to amend above calls
        # to use brick.rect

    def _off_screen(self):
        # TODO: check number of lives > 0, and set game.over flag
        # appropriately.
        sys.exit()
