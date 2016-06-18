import collections
import logging
import os

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

# Initialise the pygame modules.
pygame.init()
# Initialise the main font
MAIN_FONT = pygame.font.Font(
    os.path.join(os.path.dirname(__file__), 'data', 'fonts', 'emulogic.ttf'),
    14)


class Arkanoid:
    """Manages the overall program. This will start and end new games."""

    def __init__(self):
        # Initialise the clock.
        self._clock = pygame.time.Clock()

        # Create the main screen (the window).
        self._screen = self._create_screen()

        # Reference to a running game, when one is in play.
        self._game = None

    def main_loop(self):
        """Starts the main loop of the program which manages the screen
        interactions and game play. Pretty much everything takes place within
        this loop.
        """
        running = True

        while running:
            # Game runs at 60 fps.
            self._clock.tick(GAME_SPEED)

            # Monitor for key presses.
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    running = False

            # TODO: add logic to begin game
            if not self._game:
                self._game = Game()

            self._game.update(event_list)

            if self._game.over:
                running = False

            # Display all updates.
            pygame.display.flip()

        LOG.debug('Exiting')

    def _create_screen(self):
        screen = pygame.display.set_mode(DISPLAY_SIZE)
        pygame.display.set_caption(DISPLAY_CAPTION)
        pygame.mouse.set_visible(False)
        return screen


class Game:
    """Represents a running Arkanoid game. An instance of a Game comes into
    being when a player begins a game.
    """

    def __init__(self, lives=3):
        """Initialise a new Game with an optional number of lives.

        Args:
            lives: Optional number of lives for the player, default 3.
        """
        # Keep track of the score and lives throughout the game.
        self.score = 0
        self.lives = lives

        # The current round.
        self.round = None

        # Reference to the screen.
        self._screen = pygame.display.get_surface()

        # The raw unblitted edges are loaded once per game.
        self._edges = self._create_edges()

        # The sprites.
        self.paddle = Paddle(left_offset=self._edges.side.get_width(),
                             right_offset=self._edges.side.get_width(),
                             bottom_offset=60,
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

        # A game sequence, when set, overrides regular gameplay with a
        # predefined sequence of steps.
        self.sequence = GameStartSequence(self)

        # The number of lives displayed on the screen.
        self._life_rects = []
        # The life graphic.
        self._life_img, _ = load_png('paddle_life.png')

    def _create_edges(self):
        """Create the surfaces that represent the edges of the playable area,
        namely the top and sides.

        Returns:
            A named tuple with attributes 'side' and 'top' corresponding to
            the sides and top edges (surfaces) accordingly.
        """
        edges = collections.namedtuple('edges', 'side top')
        side_edge, _ = load_png('edge.png')
        top_edge, _ = load_png('top.png')
        return edges(side_edge, top_edge)

    def update(self, events):
        """Update the state of the running game.

        Args:
            events:
                The EventList containing the events captured since the last
                frame.
        """
        if not self.round or self.round.complete:
            self._new_round()

        self._handle_events(events)
        self._update_sprites()
        self._update_lives()

    def _new_round(self):
        """Obtain the next round and configure the ball with all the objects
        from the round that it could potentially collide with.
        """
        # Get the next round.
        if self.round is None:
            self.round = RoundOne(self._edges)
        else:
            self.round = self.round.next_round

        # Re-populate the ball with the collidable objects it needs
        # to know about.
        self.ball.remove_all_collidable_objects()
        for edge in self.round.edges:
            # Every collision with a wall momentarily increases the speed
            # of the ball.
            self.ball.add_collidable_object(edge,
                                            speed_adjust=WALL_SPEED_ADJUST)
        self.ball.add_collidable_object(
            self.paddle,
            bounce_strategy=self.paddle.bounce_strategy)

        for brick in self.round.bricks:
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
        """Erase the sprites, update their state, and then redraw them
        on the screen."""
        # Erase the previous location of the sprites.
        self._screen.blit(self.round.background, self.paddle.rect,
                          self.paddle.rect)
        self._screen.blit(self.round.background, self.ball.rect,
                          self.ball.rect)

        # Update the state of the sprites and redraw them, assuming
        # they're visible.
        self.paddle.update()
        if self.paddle.visible:
            self._screen.blit(self.paddle.image, self.paddle.rect)
        self.ball.update()
        if self.ball.visible:
            self._screen.blit(self.ball.image, self.ball.rect)

    def _on_brick_collide(self, brick):
        """Callback called by the ball when it collides with a brick.

        Args:
            brick;
                The Brick instance the ball collided with.
        """
        # Tell the ball that the brick has gone.
        self.ball.remove_collidable_object(brick)

        # Tell the round that a brick has gone, so that it can decide
        # whether the round is completed.
        self.round.brick_destroyed()

        # Erase the brick from the screen.
        self._screen.blit(self.round.background, brick, brick)

        # TODO: we need to check the brick's powerup attribiute (once brick
        # becomes a real object). If it has a powerup, initialise the powerup
        # passing in the game instance (self). Also need to amend above calls
        # to use brick.rect

    def _update_lives(self):
        """Update the number of remaining lives displayed on the screen."""
        # Erase the existing lives.
        for rect in self._life_rects:
            self._screen.blit(self.round.background, rect, rect)
        self._life_rects.clear()

        # Display the remaining lives.
        left = self._edges.side.get_width()
        top = self._screen.get_height() - self._life_img.get_height() - 10

        for life in range(self.lives - 1):
            self._life_rects.append(
                self._screen.blit(self._life_img, (left, top)))
            left += self._life_img.get_width() + 10

    def _off_screen(self):
        """Callback called by the ball when it goes offscreen. This carries
        out the actions to reduce the lives/reinitialise the sprites, or
        end the game, if there are no lives left.
        """
        # Explode the paddle immediately.
        self.paddle.explode()
        # TODO: Need to check the number of lives before doing this.
        self._sequence_coordinator = GameStartSequence(self, restart=True)


class GameStartSequence:
    """An implementation of a "game sequence" responsible for coordinating
    the sequence of events that happen when a game first starts, or restarts
    following a loss of life.
    """
    def __init__(self, game, restart=False):
        """
        Initialise the start sequence.
        Args:
            game:
                The game being started/restarted.
            restart:
                Whether the game is being restarted after a loss of life.
        """
        self._game = game
        self._restart = restart
        self._start_time = pygame.time.get_ticks()

        # Reference to the screen.
        self._screen = pygame.display.get_surface()

        # Initialise the sprite's start state.
        self._game.paddle.visible = False
        self._game.ball.visible = False
        self._game.ball.anchor(self._game.paddle,
                               self._game.paddle.rect.midtop)

    def update(self):
        if self._time_elapsed() > 1000:
            # Display the caption after a second.
            LOG.debug('Display caption')
        if self._time_elapsed() > 3000:
            # Display the "Ready" message.
            LOG.debug('Display ready message')
        if self._time_elapsed() > 3500:
            # Display the sprites.
            self._game.paddle.visible = True
            self._game.ball.visible = True
        if self._time_elapsed() > 5500:
            # Hide the text.
            LOG.debug('Hide the text and resume')
            # Release the anchor.
            self._game.ball.release(BALL_START_ANGLE_RAD)
            # Normal gameplay resumes - unset ourselves.
            self._game.sequence = None

    def _time_elapsed(self):
        now = pygame.time.get_ticks()
        return now - self._start_time


class GameIntroSequence:
    """An implementation of a "game sequence" responsible for showing the
    introduction animation when a game is first started.
    """
    def __init__(self, game):
        # TODO: this sequence will hand off to the GameStartSequence once
        # completed.
        pass


# class EndOfLifeCoordinator:
#     """An implementation of a "sequence coordinator" responsible for
#     coordinating the sequence of actions that happen when a player loses
#     a life.
#     """
#     def __init__(self, game):
#         self._game = game
#         self._start_time = clock.get_time()
#
#     def update(self):
#         # Explode the paddle immediately.
#         self._game.paddle.explode()
#
#         # Wait for the animation to complete.
#         if clock.get_time() - self._start_time > 5000:
#             # Lose a life.
#             if self._game.lives > 0:
#                 self._game.lives -= 1
#
#             if self._game.lives == 0:
#                 # Game over.
#                 self._game.over = True
#             else:
#                 # Display the caption for the current round.
#                 # TODO: workout the correct position for the text on the screen.
#                 self._screen.blit(MAIN_FONT.render(self._game.round.caption),
#                             (100, 100))
#                 if clock.get_time() - self._start_time > 6000:
#                     # Display the ready message and regenerated sprites.
#                     self._screen.blit(MAIN_FONT.render('Ready'), (100, 100))
#                     self._game.paddle.reinit()
#                     self._game.ball.reinit()





