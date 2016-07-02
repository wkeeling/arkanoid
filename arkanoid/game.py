import logging

import pygame

from arkanoid.rounds import Round1
from arkanoid.sprites.ball import Ball
from arkanoid.sprites.paddle import (EXPLODE,
                                     NORMAL,
                                     Paddle)
from arkanoid.utils import (font,
                            h_centre_pos,
                            load_png)

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
BALL_BASE_SPEED = 8  # pixels per frame
# The max speed of the ball, prevents a runaway speed when lots of rapid
# collisions.
BALL_MAX_SPEED = 15  # pixels per frame
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
        interactions and game play.

        Pretty much everything takes place within this loop.
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
    being when a player starts a new game.
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

        # Reference to the main screen.
        self._screen = pygame.display.get_surface()

        # The life graphic.
        self._life_img, _ = load_png('paddle_life.png')
        # The life graphic positions.
        self._life_rects = []

        # The current round.
        self.round = round_class()

        # The paddle and ball sprites.
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

        # The powerup sprites that drop from the bricks.
        self.powerups = []

        # The currently applied powerup, if any.
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
        # Common updates.
        self._handle_events(events)
        self._update_sprites()
        self._update_lives()

        # Delegate to the active state for specific behaviour.
        self.state.update()

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
        self._screen.blit(self.round.background,
                          self.paddle.rect,
                          self.paddle.rect)
        self._screen.blit(self.round.background,
                          self.ball.rect,
                          self.ball.rect)
        for brick in self.round.bricks:
            self._screen.blit(self.round.background,
                              brick.rect,
                              brick.rect)
        for powerup in self.powerups:
            self._screen.blit(self.round.background,
                              powerup.rect,
                              powerup.rect)

        # Update the state of the sprites and redraw them, assuming
        # they're visible.
        self.paddle.update()
        if self.paddle.visible:
            self._screen.blit(self.paddle.image, self.paddle.rect)

        self.ball.update()
        if self.ball.visible:
            self._screen.blit(self.ball.image, self.ball.rect)

        for brick in self.round.bricks:
            brick.update()
            if not brick.is_destroyed():
                self._screen.blit(brick.image, brick.rect)

        for powerup in self.powerups:
            powerup.update()
            if powerup.visible:
                self._screen.blit(powerup.image, powerup.rect)

    def _update_lives(self):
        """Update the number of remaining lives displayed on the screen."""
        # Erase the existing lives.
        for rect in self._life_rects:
            self._screen.blit(self.round.background, rect, rect)
        self._life_rects.clear()

        # Display the remaining lives.
        left = self.round.edges.left.width
        top = self._screen.get_height() - self._life_img.get_height() - 10

        for life in range(self.lives - 1):
            self._life_rects.append(
                self._screen.blit(self._life_img, (left, top)))
            left += self._life_img.get_width() + 10

    def _off_screen(self):
        """Callback called by the ball when it goes offscreen."""
        if not isinstance(self.state, BallOffScreenState):
            self.state = BallOffScreenState(self)

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

        LOG.debug('Entered {}'.format(type(self).__name__))

    def update(self):
        """Update the state.

        Sub-states must implement this to perform their state specific
        behaviour. This method is called repeatedly by the main game loop.
        """
        raise NotImplementedError('Subclasses must implement update()')

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({})'.format(class_name, self.game)


class GameStartState(BaseState):
    """This state handles the behaviour after the user has begun a new game,
    but before they actually start playing it, e.g. showing an animation
    sequence.
    """

    def __init__(self, game):
        super().__init__(game)

    def update(self):
        # TODO: implement the game intro sequence (animation).
        pass


class RoundStartState(BaseState):
    """This state handles the behaviour that happens at the very beginning of
    a round and just before the real gameplay begins."""

    def __init__(self, game):
        super().__init__(game)

        # Set the ball up with the round's collidable objects.
        self._configure_ball()

        self._start_time = None
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
            brick:
                The Brick instance the ball collided with.
        """
        # Increment the collision count.
        brick.collision_count += 1

        # Should the brick be destroyed?
        if brick.is_destroyed():
            if brick.powerup_cls:
                # There is a powerup in the brick.
                powerup = brick.powerup_cls(self.game, brick)

                # Display the powerup.
                self.game.powerups.append(powerup)

            # Tell the ball that the brick has gone.
            self.game.ball.remove_collidable_object(brick)

            # Tell the round that a brick has gone, so that it can decide
            # whether the round is completed.
            self.game.round.brick_destroyed()

            # Erase the brick from the screen.
            self._screen.blit(self.game.round.background, brick.rect,
                              brick.rect)
        else:
            # Brick not destroyed, so animate it to indicate strike.
            brick.animate()

    def update(self):
        """Handle the sequence of events that happen at the beginning of a
        round just before gameplay starts.
        """
        caption, ready = None, None

        if not self._start_time:
            self._start_time = pygame.time.get_ticks()

        if self._time_elapsed() > 1000:
            # Display the caption after a second.
            caption = self._screen.blit(self._caption, self._caption_pos)
        if self._time_elapsed() > 2500:
            # Display the "Ready" message.
            ready = self._screen.blit(self._ready, self._ready_pos)
            # Display the sprites.
            self.game.paddle.visible = True
            self.game.ball.visible = True
        if self._time_elapsed() > 4500:
            # Erase the text.
            self._screen.blit(self.game.round.background, caption, caption)
            self._screen.blit(self.game.round.background, ready, ready)
        if self._time_elapsed() > 5000:
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
    """This state handles actual gameplay itself, when the user is controlling
    the paddle and ball.
    """

    def __init__(self, game):
        super().__init__(game)

    def update(self):
        if self.game.round.complete:
            self.game.round = self.game.round.next_round()
            # TODO: do we need a RoundEndState for specific behaviour when a
            # round is ended (completed)?
            self.game.state = RoundStartState(self.game)


class BallOffScreenState(BaseState):
    """This state handles what happens when gameplay stops due to the
    ball going offscreen.
    """

    def __init__(self, game):
        super().__init__(game)

        # Track the number of update cycles.
        self._start = 0

        self._deactivated = False
        self._exploded = False

    def update(self):
        # Deactivate the active powerup if set.
        if not self._deactivated and self.game.active_powerup:
            self.game.active_powerup.deactivate()
            self._deactivated = True

        # Wait for any deactivation animation to complete.
        if not self._exploded and self._start > 20:
            # Tell the paddle to explode.
            self.game.paddle.transition(EXPLODE)
            self._exploded = True

        # Wait for the explosion animation to complete.
        if self._start > 100:
            if self.game.lives - 1 > 0:
                self.game.paddle.transition(NORMAL)
                self.game.state = RoundRestartState(self.game)
            else:
                self.game.state = GameEndState(self.game)

        self._start += 1


class RoundRestartState(RoundStartState):
    """Specialisation of RoundStartState that handles the behaviour when a
    round is restarted due to the ball going off screen.
    """

    def __init__(self, game):
        super().__init__(game)

        # The new number of lives since restarting.
        self._lives = game.lives - 1

        # Whether we've reset the paddle.
        self._paddle_reset = False

    def _configure_ball(self):
        """When restarting a round, we override _configure_ball to do nothing,
        as the ball is not reconfigured on restarts.
        """
        pass

    def update(self):
        # Run the logic in the RoundStartState first.
        super().update()

        if self._time_elapsed() > 1000:
            # Update the number of lives when we display the caption.
            self.game.lives = self._lives

        if not self._paddle_reset:
            self.game.paddle.reset()
            self._paddle_reset = True


class GameEndState(BaseState):
    """This state handles the behaviour when the game ends, either due to all
    lives being lost, or when the player successfully reaches the very end.
    """

    def __init__(self, game):
        super().__init__(game)

        # Bring the ball back onto the screen, but hide it.
        # This prevents the offscreen callback from being called again.
        game.ball.anchor(game.paddle.rect.top)
        game.ball.visible = True

        # Indicate that the game is over.
        game.over = True

    def update(self):
        pass
