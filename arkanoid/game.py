import logging

import pygame

from arkanoid.event import receiver
from arkanoid.rounds import Round1
from arkanoid.sprites.ball import Ball
from arkanoid.sprites.paddle import Paddle
from arkanoid.util import (font,
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
BALL_TOP_SPEED = 15  # pixels per frame
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

        # Whether we're running.
        self._running = True

        # Set up the top level event handlers.
        def quit_handler(event):
            self._running = False
        receiver.register_handler(pygame.QUIT, quit_handler)

    def main_loop(self):
        """Starts the main loop of the program which manages the screen
        interactions and game play.

        Pretty much everything takes place within this loop.
        """
        while self._running:
            # Game runs at 60 fps.
            self._clock.tick(GAME_SPEED)

            # Receive and dispatch events.
            receiver.receive()

            # TODO: add logic to begin game
            if not self._game:
                self._game = Game()

            self._game.update()

            if self._game.over:
                self._running = False

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
                         top_speed=BALL_TOP_SPEED,
                         normalisation_rate=BALL_SPEED_NORMALISATION_RATE,
                         off_screen_callback=self._off_screen)

        # The powerup sprites that drop from the bricks.
        self.powerups = []

        # The currently applied powerup, if any.
        self.active_powerup = None

        # Other sprites which can be brought into the game can be added here.
        self.other_sprites = []

        # Create event handlers required by the game.
        self._create_event_handlers()

        # Whether the game is finished.
        self.over = False

        # The current game state.
        self.state = GameStartState(self)

    def update(self):
        """Update the state of the running game."""
        # Common updates.
        self._update_sprites()
        self._update_lives()

        # Delegate to the active state for specific behaviour.
        self.state.update()

    def _update_sprites(self):
        """Erase the sprites, update their state, and then redraw them
        on the screen."""
        sprites = [self.paddle, self.ball]
        sprites += self.round.bricks
        sprites += self.powerups
        sprites += self.other_sprites

        # Erase.
        for sprite in sprites:
            self._screen.blit(self.round.background, sprite.rect, sprite.rect)

        # Update and redraw, if visible.
        for sprite in sprites:
            sprite.update()
            if sprite.visible:
                self._screen.blit(sprite.image, sprite.rect)

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

    def on_brick_collide(self, brick):
        """Called by a sprite when it collides with a brick.

        In this case a sprite might be the ball, or a laser beam from the
        laser paddle.

        Args:
            brick:
                The Brick instance the sprite collided with.
        """
        # Increment the collision count.
        brick.collision_count += 1

        # Has the brick been destroyed, based on the collision count?
        if brick.visible:
            # Still visible, so animate to indicate strike.
            brick.animate()
        else:
            # Brick has been destroyed.
            if brick.powerup_cls:
                # There is a powerup in the brick.
                powerup = brick.powerup_cls(self, brick)

                # Display the powerup.
                self.powerups.append(powerup)

            # Tell the ball that the brick has gone.
            self.ball.remove_collidable_object(brick)

            # Tell the round that a brick has gone, so that it can decide
            # whether the round is completed.
            self.round.brick_destroyed()

    def _off_screen(self):
        """Callback called by the ball when it goes offscreen."""
        if not isinstance(self.state, BallOffScreenState):
            self.state = BallOffScreenState(self)

    def _create_event_handlers(self):
        """Create the event handlers for paddle movement."""
        def move_left(event):
            if event.key == pygame.K_LEFT:
                self.paddle.move_left()
        self.handler_move_left = move_left

        def move_right(event):
            if event.key == pygame.K_RIGHT:
                self.paddle.move_right()
        self.handler_move_right = move_right

        def stop(event):
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                self.paddle.stop()
        self.handler_stop = stop

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
        return '{}({!r})'.format(class_name, self.game)


class GameStartState(BaseState):
    """This state handles the behaviour after the user has begun a new game,
    but before they actually start playing it, e.g. showing an animation
    sequence.
    """

    def __init__(self, game):
        super().__init__(game)

        # The ball and paddle are kept invisible at the very start.
        self.game.paddle.visible = False
        self.game.ball.visible = False

        # Register the event handlers for paddle control.
        receiver.register_handler(pygame.KEYDOWN,
                                  self.game.handler_move_left,
                                  self.game.handler_move_right)
        receiver.register_handler(pygame.KEYUP, self.game.handler_stop)

    def update(self):
        # TODO: implement the game intro sequence (animation).
        self.game.state = RoundStartState(self.game)


class RoundStartState(BaseState):
    """This state handles the behaviour that happens at the very beginning of
    a round and just before the real gameplay begins."""

    def __init__(self, game):
        super().__init__(game)

        # Set the ball up with the round's collidable objects.
        self._configure_ball()

        # Keep track of the number of update cycles.
        self._update_count = 0
        self._screen = pygame.display.get_surface()

        # Initialise the sprites' start state.
        self.game.ball.reset()
        self.game.paddle.visible = False
        self.game.ball.visible = False
        # Anchor the ball to the paddle.
        self.game.ball.anchor(self.game.paddle,
                              (self.game.paddle.rect.width // 2,
                               -self.game.paddle.rect.height))

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
            bounce_strategy=self.game.paddle.bounce_strategy,
            on_collide=self.game.paddle.on_ball_collide)

        for brick in self.game.round.bricks:
            # Make the ball aware of the bricks it might collide with.
            # Every brick collision momentarily increases the speed of
            # the ball.
            self.game.ball.add_collidable_object(
                brick,
                speed_adjust=BRICK_SPEED_ADJUST,
                on_collide=self.game.on_brick_collide)

    def update(self):
        """Handle the sequence of events that happen at the beginning of a
        round just before gameplay starts.
        """
        caption, ready = None, None

        if self._update_count > 60:
            # Display the caption after a short delay.
            caption = self._screen.blit(self._caption, self._caption_pos)
        if self._update_count > 150:
            # Display the "Ready" message.
            ready = self._screen.blit(self._ready, self._ready_pos)
            # Display the sprites.
            self.game.paddle.visible = True
            self.game.ball.visible = True
        if self._update_count > 270:
            # Erase the text.
            self._screen.blit(self.game.round.background, caption, caption)
            self._screen.blit(self.game.round.background, ready, ready)
        if self._update_count > 300:
            # Release the anchor.
            self.game.ball.release()
            # Normal gameplay begins.
            self.game.state = RoundPlayState(self.game)

        self._update_count += 1

        # Don't let the paddle move when it's not displayed.
        if not self.game.paddle.visible:
            self.game.paddle.stop()


class RoundPlayState(BaseState):
    """This state handles actual gameplay itself, when the user is controlling
    the paddle and ball.
    """

    def __init__(self, game):
        super().__init__(game)

    def update(self):
        if self.game.round.complete:
            self.game.round = self.game.round.next_round()
            self.game.state = RoundStartState(self.game)


class BallOffScreenState(BaseState):
    """This state handles what happens when gameplay stops due to the
    ball going offscreen.
    """

    def __init__(self, game):
        super().__init__(game)

        # Deactivate the active powerup if set.
        if self.game.active_powerup:
            self.game.active_powerup.deactivate()
            self.game.active_powerup = None

        # Tell the paddle to explode.
        self.game.paddle.explode(on_complete=self._exploded)
        self._explode_complete = False

    def update(self):
        # Wait for the explosion animation to complete.
        if self._explode_complete:
            if self.game.lives - 1 > 0:
                self.game.state = RoundRestartState(self.game)
            else:
                self.game.state = GameEndState(self.game)

    def _exploded(self):
        self._explode_complete = True


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

        if self._update_count > 60:
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
        game.ball.anchor(game.paddle.rect.midtop)
        game.ball.visible = False

        # Indicate that the game is over.
        game.over = True

        # Unregister the event handlers.
        receiver.unregister_handler(self.game.handler_move_left,
                                    self.game.handler_move_right,
                                    self.game.handler_stop)

    def update(self):
        pass
