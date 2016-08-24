import logging
import random

import pygame

from arkanoid.event import receiver
from arkanoid.rounds.round1 import Round1
from arkanoid.sprites.edge import (DOOR_TOP_LEFT,
                                   DOOR_TOP_RIGHT)
from arkanoid.sprites.enemy import (Enemy,
                                    EnemyType)
from arkanoid.sprites.ball import Ball
from arkanoid.sprites.paddle import (ExplodingState,
                                     Paddle,
                                     MaterializeState)
from arkanoid.util import (font,
                           h_centre_pos,
                           load_high_score,
                           load_png,
                           save_high_score)

LOG = logging.getLogger(__name__)

# The speed the game runs at in FPS.
GAME_SPEED = 60
# The dimensions of the main game window in pixels.
DISPLAY_SIZE = 600, 800
# The number of pixels from the top of the screen before the top edge starts.
TOP_OFFSET = 150
# The title of the main window.
DISPLAY_CAPTION = 'Arkanoid'
# The angle the ball initially moves off the paddle, in radians.
BALL_START_ANGLE_RAD = 5.0  # Value must be no smaller than -3.14
# The speed that the ball will always try to arrive at.
BALL_BASE_SPEED = 9  # pixels per frame
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

        # Create the main screen (the window) and default background.
        self._screen = self._create_screen()
        self._background = self._create_background()
        self._display_logo()
        self._display_score_titles()
        self._display_score(0)
        self._high_score = load_high_score()
        self._display_highscore(self._high_score)

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
            self._display_score(self._game.score)

            if self._game.over:
                if self._game.score > self._high_score:
                    self._high_score = self._game.score
                    self._display_highscore(self._high_score)
                    save_high_score(self._high_score)
                self._running = False

            # Display all updates.
            pygame.display.flip()

        LOG.debug('Exiting')

    def _create_screen(self):
        pygame.display.set_mode(DISPLAY_SIZE)
        pygame.display.set_caption(DISPLAY_CAPTION)
        pygame.mouse.set_visible(False)
        screen = pygame.display.get_surface()
        return screen

    def _create_background(self):
        background = pygame.Surface(self._screen.get_size())
        background = background.convert()
        background.fill((0, 0, 0))
        return background

    def _display_logo(self):
        image, _ = load_png('logo.png')
        self._screen.blit(image, (5, 0))

    def _display_score_titles(self):
        player = font(MAIN_FONT, 18).render('1UP', False, (230, 0, 0))
        self._screen.blit(player, (self._screen.get_width() -
                                   player.get_width() - 10, 10))
        high_score = font(MAIN_FONT, 18).render('HIGH SCORE', False,
                                                (230, 0, 0))
        self._screen.blit(high_score, (self._screen.get_width() -
                                       high_score.get_width() - 10, 75))

    def _display_score(self, value):
        score = font(MAIN_FONT, 18).render(str(value), False, (255, 255, 255))
        position = self._screen.get_width() - score.get_width() - 10, 35
        self._screen.blit(self._background, position, score.get_rect())
        self._screen.blit(score, position)

    def _display_highscore(self, value):
        high_score = font(MAIN_FONT, 18).render(str(value), False,
                                                (255, 255, 255))
        position = self._screen.get_width() - high_score.get_width() - 10, 100
        self._screen.blit(self._background, position, high_score.get_rect())
        self._screen.blit(high_score, position)


class Game:
    """Represents a running Arkanoid game. An instance of a Game comes into
    being when a player starts a new game.
    """

    def __init__(self, round_class=Round1, lives=3):
        """Initialise a new Game.

        Args:
            round_class:
                The class of the round to start, default Round1.
            lives:
                Optional number of lives for the player, default 3.
        """
        # Keep track of the score and lives throughout the game.
        self.lives = lives
        self.score = 0

        # Reference to the main screen.
        self._screen = pygame.display.get_surface()

        # The life graphic.
        self._life_img, _ = load_png('paddle_life.png')
        # The life graphic positions.
        self._life_rects = []

        # The current round.
        self.round = round_class(TOP_OFFSET)

        # The sprites in the game.
        self.paddle = Paddle(left_offset=self.round.edges.left.rect.width,
                             right_offset=self.round.edges.right.rect.width,
                             bottom_offset=60,
                             speed=PADDLE_SPEED)

        ball = Ball(start_pos=self.paddle.rect.midtop,
                    start_angle=BALL_START_ANGLE_RAD,
                    base_speed=BALL_BASE_SPEED,
                    top_speed=BALL_TOP_SPEED,
                    normalisation_rate=BALL_SPEED_NORMALISATION_RATE,
                    off_screen_callback=self._off_screen)

        # The game starts with a single ball in play initially.
        self.balls = [ball]

        # The currently applied powerup, if any.
        self.active_powerup = None

        # The current enemies in the game.
        self.enemies = []

        # Hold a reference to all the sprites for redrawing purposes.
        self.sprites = []

        # Create event handlers required by the game.
        self._create_event_handlers()

        # Whether the game is finished.
        self.over = False

        # The current game state which handles the behaviour for the
        # current stage of the game.
        self.state = GameStartState(self)

    def update(self):
        """Update the state of the running game."""
        # Delegate to the active state. This determines the behaviour
        # for the current stage of the game.
        self.state.update()

        # Re-render the sprites.
        self._update_sprites()
        self._update_lives()

    def _update_sprites(self):
        """Erase the sprites, update their state, and then redraw them
        on the screen."""
        # Erase.
        for sprite in self.sprites:
            self._screen.blit(self.round.background, sprite.rect, sprite.rect)

        # Update and redraw, if visible.
        for sprite in self.sprites:
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
        left = self.round.edges.left.rect.width
        top = self._screen.get_height() - self._life_img.get_height() - 5

        for life in range(self.lives - 1):
            self._life_rects.append(
                self._screen.blit(self._life_img, (left, top)))
            left += self._life_img.get_width() + 5

    def on_brick_collide(self, brick, sprite):
        """Called by a sprite when it collides with a brick.

        In this case a sprite might be the ball, or a laser beam from the
        laser paddle.

        Args:
            brick:
                The Brick instance the sprite collided with.
            sprite:
                The sprite instance that struck the brick.
        """
        # Increment the collision count.
        brick.collision_count += 1

        # Has the brick been destroyed, based on the collision count?
        if brick.visible:
            # Still visible, so animate to indicate strike.
            brick.animate()
        else:
            # Brick has been destroyed.
            if brick.value:
                # Add this brick's value to the score.
                self.score += brick.value

            # Tell the round that a brick has gone, so that it can decide
            # whether the round is completed.
            self.round.brick_destroyed()

        if brick.powerup_cls:
            # There is a powerup in the brick.
            # Figure out whether we should release it.
            release = not brick.visible  # Always release on brick destruction

            if not release:
                # Brick hasn't been destroyed, so randomly decide whether
                # to release or not.
                release = random.choice((True, False))

            if release:
                powerup = brick.powerup_cls(self, brick)
                brick.powerup_cls = None

                # Display the powerup.
                self.sprites.append(powerup)

        if not self.enemies and self.round.can_release_enemies():
            # Setup the enemy sprites.
            self._setup_enemies()

            # Release them into the game.
            # Note that once an enemy is destroyed, it will call
            # Game.release_enemy() itself to respawn itself.
            for enemy in self.enemies:
                self.release_enemy(enemy)

    def on_enemy_collide(self, enemy, sprite):
        """Called by a sprite when it collides with an enemy.

        In this case a sprite might be the ball, or a laser beam from the
        laser paddle.

        Args:
            enemy:
                The Enemy instance the sprite collided with.
            sprite:
                The sprite instance that struck the enemy.
        """
        enemy.explode()
        self.score += 500

    def _setup_enemies(self):
        """Set up the enemy sprites ready for release into the game."""
        collidable_sprites = []
        collidable_sprites += self.round.edges
        collidable_sprites += self.round.bricks

        for _ in range(self.round.num_enemies):
            # Enemies can collide with one another.
            collidable_sprites += self.enemies

            # Create the sprite.
            enemy_sprite = Enemy(self.round.enemy_type,
                                 self.paddle,
                                 self.on_enemy_collide,
                                 collidable_sprites,
                                 on_destroyed=self.release_enemy)

            # Keep track of the enemy sprites currently in the game.
            self.enemies.append(enemy_sprite)

            # Allow the sprite to be displayed.
            self.sprites.append(enemy_sprite)

    def release_enemy(self, enemy):
        """Release an enemy through one of the top doors.

        This method will select a top door at random, open it and then
        release the enemy sprite through it before closing it.

        Note that the door does not open immediately. A random delay occurs
        before the door opens.

        Args:
            enemy:
                The enemy sprite to release through one of the doors.
        """
        # Conceal the enemy until the door opens.
        enemy.conceal()
        # Randomly select the door we use.
        door = random.choice((DOOR_TOP_LEFT, DOOR_TOP_RIGHT))

        def on_enemy_collide_ball(enemy, ball):
            self.on_enemy_collide(enemy, ball)
            ball.remove_collidable_sprite(enemy)

        def door_open(coords):
            enemy.reset()  # Show the enemy and re-init its movement.
            enemy.rect.topleft = coords
            # Tell the ball about it.
            self.ball.add_collidable_sprite(enemy,
                                            on_collide=on_enemy_collide_ball)

        # Trigger opening the door.
        self.round.edges.top.open_door(door, on_open=door_open)

    def _off_screen(self, ball):
        """Callback called by a ball when it goes offscreen.

        Args:
            ball:
                The ball that left the screen.
        """
        if len(self.balls) > 1:
            # There are multiple balls in play, so just take this ball
            # out of play.
            self.balls.remove(ball)
            self.sprites.remove(ball)
            ball.visible = False
        else:
            # This ball is the last in play, so transition to the
            # BallOffScreenState which handles end of life.
            if not isinstance(self.state, BallOffScreenState):
                self.state = BallOffScreenState(self)

    def _create_event_handlers(self):
        """Create the event handlers for paddle movement."""
        keys_down = 0

        def move_left(event):
            nonlocal keys_down
            if event.key == pygame.K_LEFT:
                self.paddle.move_left()
                keys_down += 1
        self.handler_move_left = move_left

        def move_right(event):
            nonlocal keys_down
            if event.key == pygame.K_RIGHT:
                self.paddle.move_right()
                keys_down += 1
        self.handler_move_right = move_right

        def stop(event):
            nonlocal keys_down
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                if keys_down > 0:
                    keys_down -= 1
                if keys_down == 0:
                    self.paddle.stop()
        self.handler_stop = stop

    @property
    def ball(self):
        """A convenience attribute for accessing the primary ball in the game.

        This is really just an convenient alias so client code doesn't have to
        do game.balls[0] everywhere.

        Returns:
            The priamry ball in the game, or None if no balls currently in
            play.
        """
        try:
            return self.balls[0]
        except IndexError:
            return None

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
    a round and just before the real gameplay begins.

    This state initialises the sprites so they are set up ready for a new
    round to begin.
    """

    def __init__(self, game):
        super().__init__(game)

        # Set up the sprites for the round.
        self._setup_sprites()

        # Set the ball up with the round's collidable objects.
        self._configure_ball()

        # Initialise the sprites' display state.
        self._screen = pygame.display.get_surface()
        self.game.ball.reset()
        self.game.paddle.visible = False
        self.game.ball.visible = False
        # Anchor the ball whilst it's invisible.
        self.game.ball.anchor((self._screen.get_width() / 2,
                               self._screen.get_height() - 100))

        # Initialise the text.
        self._caption = font(MAIN_FONT, 18).render(self.game.round.name,
                                                   False, (255, 255, 255))
        self._caption_pos = (h_centre_pos(self._caption),
                             self.game.paddle.rect.center[1] - 150)
        self._ready = font(MAIN_FONT, 18).render('Ready', False,
                                                 (255, 255, 255))
        self._ready_pos = (h_centre_pos(self._ready),
                           self._caption_pos[1] + 50)

        # Deactivate any active powerup.
        if self.game.active_powerup:
            self.game.active_powerup.deactivate()

        # Whether we've reset the paddle
        self._paddle_reset = False

        # Keep track of the number of update cycles.
        self._update_count = 0

    def _setup_sprites(self):
        """Make all the sprites available for rendering."""
        self.game.sprites.clear()
        self.game.sprites.append(self.game.paddle)
        self.game.sprites.append(self.game.ball)
        self.game.sprites += self.game.round.edges
        self.game.sprites += self.game.round.bricks

    def _configure_ball(self):
        """Configure the ball with all the objects from the current round
        that it could potentially collide with.
        """
        self.game.ball.remove_all_collidable_sprites()

        for edge in self.game.round.edges:
            # Every collision with a wall momentarily increases the speed
            # of the ball.
            self.game.ball.add_collidable_sprite(
                edge,
                speed_adjust=WALL_SPEED_ADJUST)

        self.game.ball.add_collidable_sprite(
            self.game.paddle,
            bounce_strategy=self.game.paddle.bounce_strategy,
            on_collide=self.game.paddle.on_ball_collide)

        for brick in self.game.round.bricks:
            # Make the ball aware of the bricks it might collide with.
            # Every brick collision momentarily increases the speed of
            # the ball.
            self.game.ball.add_collidable_sprite(
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
            # Anchor the ball to the paddle.
            self.game.ball.anchor(self.game.paddle,
                                  (self.game.paddle.rect.width // 2,
                                   -self.game.ball.rect.height))
            # Display the sprites.
            if not self._paddle_reset:
                self.game.paddle.reset()
                self._paddle_reset = True
            self.game.paddle.visible = True
            self.game.ball.visible = True
        if self._update_count == 151:
            # Animate the paddle materializing onto the screen.
            self.game.paddle.transition(MaterializeState(self.game.paddle))
        if self._update_count > 270:
            # Erase the text.
            self._screen.blit(self.game.round.background, caption, caption)
            self._screen.blit(self.game.round.background, ready, ready)
        if self._update_count > 300:
            # Release the anchor.
            self.game.ball.release(BALL_START_ANGLE_RAD)
            # Normal gameplay begins.
            self.game.state = RoundPlayState(self.game)

        self._update_count += 1

        # Don't let the paddle move when it's not displayed.
        if not self.game.paddle.visible:
            self.game.paddle.stop()


class RoundPlayState(BaseState):
    """This state is active when the game is running and the user is
    controlling the paddle and ball.
    """

    def __init__(self, game):
        super().__init__(game)

    def update(self):
        if self.game.round.complete:
            self.game.state = RoundEndState(self.game)


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
        self.game.paddle.transition(
            ExplodingState(self.game.paddle, self._exploded))
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

        # Conceal any enemy sprites.
        for enemy in self.game.enemies:
            enemy.conceal()

        # Cancel any existing open door requests.
        self.game.round.edges.top.cancel_open_door()

        # Whether the enemies have been re-released for this round restart.
        self._enemies_rereleased = False

    def _setup_sprites(self):
        """No need to setup the sprites again on round restart."""
        pass

    def _configure_ball(self):
        """No need to configure the ball again on round restart."""
        pass

    def update(self):
        # Run the logic in the RoundStartState first.
        super().update()

        if self._update_count > 60:
            # Update the number of lives when we display the caption.
            self.game.lives = self._lives
        if self._update_count > 300:
            # Re-release any enemies that were previously active.
            if not self._enemies_rereleased:
                for enemy in self.game.enemies:
                    self.game.release_enemy(enemy)
                self._enemies_rereleased = True


class RoundEndState(BaseState):
    """This state handles the behaviour when the round ends (is completed
    successfully).
    """
    def __init__(self, game):
        super().__init__(game)

        self._update_count = 0

    def update(self):
        for ball in self.game.balls:
            ball.speed = 0
            ball.visible = False

        self.game.paddle.visible = False

        for enemy in self.game.enemies:
            enemy.visible = False
        self.game.enemies.clear()

        # Pause for a short period after stopping the ball(s).
        if self._update_count > 120:
            # Move on to the next round, carrying over a single ball.
            self.game.balls = self.game.balls[:1]
            self.game.round = self.game.round.next_round(TOP_OFFSET)
            self.game.state = RoundStartState(self.game)

        self._update_count += 1


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
