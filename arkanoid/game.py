import logging

import pygame

from arkanoid.rounds import Round1
from arkanoid.sprites import Ball
from arkanoid.sprites import ExplodingPaddle
from arkanoid.sprites import Paddle
from arkanoid.utils import font
from arkanoid.utils import h_centre_pos
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
# The main font.
MAIN_FONT = 'emulogic.ttf'

# Initialise the pygame modules.
pygame.init()


class Arkanoid:
    """Manages the overall program. This will start and end new games."""

    def __init__(self):
        # Initialise the clock.
        self._clock = pygame.time.Clock()

        # Create the main screen (the window).
        self._create_screen()

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

    def __init__(self, round_class=Round1, lives=3):
        """Initialise a new Game with an optional level (aka 'round'), and
        optional number of lives.

        Args:
            round_class: The class of the round to start, default Round1.
            lives: Optional number of lives for the player, default 3.
        """
        # Keep track of the score and lives throughout the game.
        self.score = 0
        self.lives = lives

        # The life graphic.
        self.life_img, _ = load_png('paddle_life.png')
        # The life graphic positions.
        self.life_rects = []

        # The current round.
        self.round = round_class()

        # The "permanent" sprites.
        self.paddle = Paddle(left_offset=self.round.edges.left.width,
                             right_offset=self.round.edges.right.width,
                             bottom_offset=60,
                             speed=PADDLE_SPEED)

        self.ball = Ball(start_pos=self.paddle.rect.midtop,
                         start_angle=BALL_START_ANGLE_RAD,
                         base_speed=BALL_BASE_SPEED,
                         max_speed=BALL_MAX_SPEED,
                         normalisation_rate=BALL_SPEED_NORMALISATION_RATE,
                         off_screen_callback=self._off_screen)

        # Other sprites that can enter the game.
        self.other_sprites = []

        # The current powerup, if any.
        self.active_powerup = None

        # Whether the game is finished.
        self.over = False

        # The current game state.
        self.state = RoundStartState(self)

    def update(self, events):
        """Update the state of the running game.

        Args:
            events:
                The EventList containing the events captured since the last
                frame.
        """
        # We just delegate to the active state.
        self.state.update(events)

    def _off_screen(self):
        """Callback called by the ball when it goes offscreen. This carries
        out the actions to reduce the lives/reinitialise the sprites, or
        end the game, if there are no lives left.
        """
        # # Explode the paddle immediately.
        # self.paddle.explode()
        # TODO: Need to check the number of lives before doing this.
        # Should be RoundRestartState()
        if self.lives - 1 > 0:
            self.state = RoundRestartState(self)
        else:
            # TODO: possible lose "over" and transition to a GameEndState.
            self.over = True

    def __repr__(self):
        class_name = type(self).__name__
        return '{}(round_class={}, lives={})'.format(
            class_name,
            type(self.round).__name__,
            self.lives)


class BaseState:
    """Abstract base class holding behaviour common to all states."""

    def __init__(self, game):
        self.game = game
        self.screen = pygame.display.get_surface()

    def update(self, events):
        """Update the state. This method is called repeatedly by the main
        game loop.

        Args:
            events:
                The EventList containing the events captured since the last
                frame.
        """
        self._handle_events(events)
        self._update_sprites()
        self._update_lives()
        self._do_update()

    def _handle_events(self, event_list):
        for event in event_list:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.game.paddle.move_left()
                elif event.key == pygame.K_RIGHT:
                    self.game.paddle.move_right()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    self.game.paddle.stop()

    def _update_sprites(self):
        """Erase the sprites, update their state, and then redraw them
        on the screen."""
        # Erase the previous location of the sprites.
        self.screen.blit(self.game.round.background,
                         self.game.paddle.rect,
                         self.game.paddle.rect)
        self.screen.blit(self.game.round.background,
                         self.game.ball.rect,
                         self.game.ball.rect)
        for sprite in self.game.other_sprites:
            self.screen.blit(self.game.round.background,
                             sprite.rect, sprite.rect)

        # Update the state of the sprites and redraw them, assuming
        # they're visible.
        self.game.paddle.update()
        if self.game.paddle.visible:
            self.screen.blit(self.game.paddle.image, self.game.paddle.rect)
        self.game.ball.update()
        if self.game.ball.visible:
            self.screen.blit(self.game.ball.image, self.game.ball.rect)
        for sprite in self.game.other_sprites:
            sprite.update()
            self.screen.blit(sprite.image, sprite.rect)

    def _update_lives(self):
        """Update the number of remaining lives displayed on the screen."""
        # Erase the existing lives.
        for rect in self.game.life_rects:
            self.screen.blit(self.game.round.background, rect, rect)
        self.game.life_rects.clear()

        # Display the remaining lives.
        left = self.game.round.edges.left.width
        top = self.screen.get_height() - self.game.life_img.get_height() - 10

        for life in range(self.game.lives - 1):
            self.game.life_rects.append(
                self.screen.blit(self.game.life_img, (left, top)))
            left += self.game.life_img.get_width() + 10

    def _do_update(self):
        """Abstract hook method called by update() that sub states must
        implement to perform their state specific behaviour.
        """
        raise NotImplementedError('Subclasses must implement do_update()')

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({})'.format(class_name, self.game)


class RoundStartState(BaseState):

    def __init__(self, game):
        super().__init__(game)

        # Set the ball up with the round's collidable objects.
        self._configure_ball()

        self._start_time = pygame.time.get_ticks()
        self._screen = pygame.display.get_surface()

        # Initialise the sprites' start state.
        self.game.paddle.visible = False
        self.game.ball.visible = False
        paddle_width = self.game.paddle.rect.width
        paddle_height = self.game.paddle.rect.height
        # Anchor the ball to the paddle.
        self.game.ball.anchor(self.game.paddle,
                              (paddle_width // 2, -paddle_height))

        # Initialise the text.
        self._caption = font(MAIN_FONT, 18).render(self.game.round.caption,
                                                   False, (255, 255, 255))
        screen_height = self._screen.get_height()
        self._caption_pos = (h_centre_pos(self._caption),
                             screen_height - (screen_height * 0.4))
        self._ready = font(MAIN_FONT, 18).render('Ready', False,
                                                 (255, 255, 255))
        self._ready_pos = (h_centre_pos(self._ready),
                           self._caption_pos[1] + 50)

    def _configure_ball(self):
        """Configure the ball with all the objects from the current round
        that it could potentially collide with.
        """
        self.game.ball.remove_all_collidable_objects()
        for edge in self.game.round.edges:
            # Every collision with a wall momentarily increases the speed
            # of the ball.
            self.game.ball.add_collidable_object(
                edge,
                speed_adjust=WALL_SPEED_ADJUST)
        self.game.ball.add_collidable_object(
            self.game.paddle,
            bounce_strategy=self.game.paddle.bounce_strategy)

        for brick in self.game.round.bricks:
            # Make the ball aware of the bricks it might collide with.
            # Every brick collision momentarily increases the speed of
            # the ball.
            self.game.ball.add_collidable_object(
                brick,
                speed_adjust=BRICK_SPEED_ADJUST,
                on_collide=self._on_brick_collide)

    def _on_brick_collide(self, brick):
        """Callback called by the ball when it collides with a brick.

        Args:
            brick;
                The Brick instance the ball collided with.
        """
        # Tell the ball that the brick has gone.
        self.game.ball.remove_collidable_object(brick)

        # Tell the round that a brick has gone, so that it can decide
        # whether the round is completed.
        self.game.round.brick_destroyed()

        # Erase the brick from the screen.
        self._screen.blit(self.game.round.background, brick, brick)

        # TODO: we need to check the brick's powerup attribiute (once brick
        # becomes a real object). If it has a powerup, initialise the powerup
        # passing in the game instance (self). Also need to amend above calls
        # to use brick.rect

    def _do_update(self):
        caption, ready = None, None

        if self._time_elapsed() > 1000:
            # Display the caption after a second.
            caption = self._screen.blit(self._caption, self._caption_pos)
        if self._time_elapsed() > 3000:
            # Display the "Ready" message.
            ready = self._screen.blit(self._ready, self._ready_pos)
            # Display the sprites.
            self.game.paddle.visible = True
            self.game.ball.visible = True
        if self._time_elapsed() > 5500:
            # Erase the text.
            self._screen.blit(self.game.round.background, caption, caption)
            self._screen.blit(self.game.round.background, ready, ready)
            # Release the anchor.
            self.game.ball.release(BALL_START_ANGLE_RAD)
            # Normal gameplay begins.
            self.game.state = RoundPlayState(self.game)

        # Don't let the paddle move when it's not displayed.
        if not self.game.paddle.visible:
            self.game.paddle.stop()

    def _time_elapsed(self):
        now = pygame.time.get_ticks()
        return now - self._start_time


class RoundPlayState(BaseState):

    def __init__(self, game):
        super().__init__(game)

    def _do_update(self):
        if self.game.round.complete:
            self.game.round = self.game.round.next_round()
            self.game.state = RoundStartState(self.game)


class RoundRestartState(RoundStartState):

    def __init__(self, game):
        super().__init__(game)

        # Whether to update our state.
        self._update = False

        # The new number of lives since restarting.
        self._lives = game.lives - 1

        # Keep track of the existing paddle.
        self._paddle = game.paddle
        self._paddle_reset = False

        # Temporarily substitute the exploding paddle into the game.
        game.paddle = ExplodingPaddle(game.paddle,
                                      on_complete=self._on_explosion_finished)

    def _configure_ball(self):
        """When restarting a round, we override _configure_ball to do nothing,
        as the ball is not reconfigured on restarts.
        """
        pass

    def _do_update(self):
        if self._update:
            super()._do_update()

            if self._time_elapsed() > 1000:
                # Update the number of lives when we display the caption.
                self.game.lives = self._lives

            if not self._paddle_reset:
                self.game.paddle.reset()
                self._paddle_reset = True

    def _on_explosion_finished(self):
        # Put back the real paddle.
        self.game.paddle = self._paddle

        # Allow the rest of this restart state to execute.
        self._update = True


class GameStartState(BaseState):

    def __init__(self, game):
        super().__init__(game)

    def _do_update(self):
        # TODO: implement the game intro sequence (animation).
        pass
