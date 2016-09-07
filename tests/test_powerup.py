from unittest import TestCase
from unittest.mock import (Mock,
                           patch)

from arkanoid.sprites.powerup import (CatchPowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      PowerUp,
                                      SlowBallPowerUp)


class TestPowerUp(TestCase):
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_init_loads_png_sequence(self, mock_pygame,
                                     mock_load_png_sequence):
        PowerUp(Mock(), Mock(), 'test_prefix')

        mock_load_png_sequence.assert_called_once_with('test_prefix')

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_init_positions_powerup(self, mock_pygame,
                                    mock_load_png_sequence):
        mock_brick = Mock()
        mock_brick.rect.bottomleft = (10, 10)
        mock_brick.rect.width = 50
        mock_brick.rect.height = 10
        PowerUp(Mock(), mock_brick, 'test_prefix')

        mock_pygame.Rect.assert_called_once_with((10, 10), (50, 10))

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_update_moves_powerup(self, mock_pygame,
                                  mock_load_png_sequence):
        mock_image = Mock()
        mock_load_png_sequence.return_value = [(mock_image, Mock())]
        mock_rect = Mock()
        mock_pygame.Rect.return_value = mock_rect
        mock_rect.move.return_value = mock_rect
        mock_screen = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_area = Mock()
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True
        powerup = PowerUp(Mock(), Mock(), 'test_prefix')

        powerup.update()

        mock_rect.move.assert_called_once_with(0, powerup._speed)
        self.assertEquals(powerup.image, mock_image)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_update_moves_powerup_offscreen(self, mock_pygame,
                                            mock_load_png_sequence):
        mock_image = Mock()
        mock_load_png_sequence.return_value = [(mock_image, Mock())]
        mock_rect = Mock()
        mock_pygame.Rect.return_value = mock_rect
        mock_rect.move.return_value = mock_rect
        mock_screen = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_area = Mock()
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = False
        mock_game = Mock()
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')

        powerup.update()

        mock_rect.move.assert_called_once_with(0, powerup._speed)
        mock_game.sprites.remove.assert_called_once_with(powerup)
        self.assertFalse(powerup.visible)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_update_animates_powerup(self, mock_pygame,
                                     mock_load_png_sequence):
        mock_image_1 = Mock()
        mock_image_2 = Mock()
        mock_load_png_sequence.return_value = [(mock_image_1, Mock()),
                                               (mock_image_2, Mock())]
        mock_rect = Mock()
        mock_pygame.Rect.return_value = mock_rect
        mock_rect.move.return_value = mock_rect
        mock_screen = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_area = Mock()
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True
        powerup = PowerUp(Mock(), Mock(), 'test_prefix')

        # The powerup image is changed every 4 cycles.
        powerup.update()
        powerup.update()
        powerup.update()
        powerup.update()

        self.assertEquals(powerup.image, mock_image_2)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_update_collision_no_activate_explode(self, mock_pygame,
                                                  mock_load_png_sequence):
        """Test that the powerup does not activate when it collides with
        the paddle but the paddle is exploding.
        """
        mock_image_1 = Mock()
        mock_image_2 = Mock()
        mock_load_png_sequence.return_value = [(mock_image_1, Mock()),
                                               (mock_image_2, Mock())]
        mock_rect = Mock()
        mock_pygame.Rect.return_value = mock_rect
        mock_rect.move.return_value = mock_rect
        mock_rect.colliderect.return_value = True
        mock_screen = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_area = Mock()
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True
        mock_game = Mock()
        mock_game.paddle.exploding = True
        mock_game.active_powerup = None
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')

        powerup.update()

        mock_rect.colliderect.assert_called_once_with(mock_game.paddle.rect)
        self.assertIsNone(mock_game.active_powerup)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_update_collision_no_activate_invisible(self, mock_pygame,
                                                    mock_load_png_sequence):
        """Test that the powerup does not activate when it collides with
        the paddle but the paddle is not visible.
        """
        mock_image_1 = Mock()
        mock_image_2 = Mock()
        mock_load_png_sequence.return_value = [(mock_image_1, Mock()),
                                               (mock_image_2, Mock())]
        mock_rect = Mock()
        mock_pygame.Rect.return_value = mock_rect
        mock_rect.move.return_value = mock_rect
        mock_rect.colliderect.return_value = True
        mock_screen = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_area = Mock()
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True
        mock_game = Mock()
        mock_game.paddle.exploding = False
        mock_game.paddle.visible = False
        mock_game.active_powerup = None
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')

        powerup.update()

        mock_rect.colliderect.assert_called_once_with(mock_game.paddle.rect)
        self.assertIsNone(mock_game.active_powerup)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_update_collision_should_activate(self, mock_pygame,
                                              mock_load_png_sequence):
        """Test that the powerup does activate when it collides with
        the paddle.
        """
        mock_image_1 = Mock()
        mock_image_2 = Mock()
        mock_load_png_sequence.return_value = [(mock_image_1, Mock()),
                                               (mock_image_2, Mock())]
        mock_rect = Mock()
        mock_pygame.Rect.return_value = mock_rect
        mock_rect.move.return_value = mock_rect
        mock_rect.colliderect.return_value = True
        mock_screen = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_area = Mock()
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True
        mock_game = Mock()
        mock_game.paddle.exploding = False
        mock_game.paddle.visible = True
        mock_active_powerup = Mock()
        mock_game.active_powerup = mock_active_powerup
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')
        mock_activate = Mock()
        powerup._activate = mock_activate

        powerup.update()

        mock_rect.colliderect.assert_called_once_with(mock_game.paddle.rect)
        mock_active_powerup.deactivate.assert_called_once_with()
        mock_activate.assert_called_once_with()
        self.assertIsNotNone(mock_game.active_powerup)
        mock_game.sprites.remove.assert_called_once_with(powerup)
        self.assertFalse(powerup.visible)


def _configure_mocks(mock_load_png_sequence, mock_pygame):
    mock_image = Mock()
    mock_load_png_sequence.return_value = [(mock_image, Mock())]
    mock_rect = Mock()
    mock_pygame.Rect.return_value = mock_rect
    mock_rect.move.return_value = mock_rect
    mock_rect.colliderect.return_value = True
    mock_screen = Mock()
    mock_pygame.display.get_surface.return_value = mock_screen
    mock_area = Mock()
    mock_screen.get_rect.return_value = mock_area
    mock_area.contains.return_value = True
    mock_game = Mock()
    mock_game.paddle.exploding = False
    mock_game.paddle.visible = True

    return mock_game


class TestExtraLifePowerUp(TestCase):
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_activate_adds_life_to_game(self, mock_pygame,
                                        mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.lives = 2
        powerup = ExtraLifePowerUp(mock_game, Mock())

        powerup.update()

        mock_load_png_sequence.assert_called_once_with('powerup_life')
        self.assertEqual(mock_game.lives, 3)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_deactivate_is_noop(self, mock_pygame,
                                mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.lives = 2
        mock_game.active_powerup = ExtraLifePowerUp(mock_game, Mock())
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')
        powerup._activate = Mock()

        powerup.update()

        self.assertEqual(mock_game.lives, 2)


class TestSlowBallPowerUp(TestCase):
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_activate_slows_all_balls(self, mock_pygame,
                                      mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.ball.base_speed = 10
        mock_game.balls = [Mock(), Mock(), Mock()]
        powerup = SlowBallPowerUp(mock_game, Mock())

        powerup.update()

        mock_load_png_sequence.assert_called_once_with('powerup_slow')
        self.assertEqual(len(mock_game.balls), 3)
        for ball in mock_game.balls:
            self.assertEqual(ball.speed, SlowBallPowerUp._SLOW_BALL_SPEED)
            self.assertEqual(ball.base_speed, SlowBallPowerUp._SLOW_BALL_SPEED)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_deactivate_reinstates_ball_speed(self, mock_pygame,
                                              mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.active_powerup = SlowBallPowerUp(mock_game, Mock())
        mock_game.active_powerup._orig_speed = 10
        mock_game.balls = [Mock(), Mock(), Mock()]
        for ball in mock_game.balls:
            ball.speed = SlowBallPowerUp._SLOW_BALL_SPEED
            ball.base_speed = SlowBallPowerUp._SLOW_BALL_SPEED
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')
        powerup._activate = Mock()

        powerup.update()

        self.assertEqual(len(mock_game.balls), 3)
        for ball in mock_game.balls:
            self.assertEqual(ball.speed, 10)
            self.assertEqual(ball.base_speed, 10)


class TestExpandPowerUp(TestCase):

    @patch('arkanoid.sprites.powerup.WideState')
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_activate_transitions_to_wide_state(self, mock_pygame,
                                                mock_load_png_sequence,
                                                mock_wide_state):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_state = Mock()
        mock_wide_state.return_value = mock_state
        mock_game.balls = [Mock(), Mock(), Mock()]
        for ball in mock_game.balls:
            ball.base_speed = 10
        powerup = ExpandPowerUp(mock_game, Mock())

        powerup.update()

        mock_load_png_sequence.assert_called_once_with('powerup_expand')
        mock_game.paddle.transition.assert_called_once_with(mock_state)
        self.assertEqual(len(mock_game.balls), 3)
        for ball in mock_game.balls:
            self.assertEqual(ball.base_speed, 11)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_no_activate_when_already_expand(self, mock_pygame,
                                             mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.active_powerup = ExpandPowerUp(mock_game, Mock())
        powerup = ExpandPowerUp(mock_game, Mock())
        powerup._activate = Mock()

        powerup.update()

        self.assertEqual(powerup._activate.call_count, 0)

    @patch('arkanoid.sprites.powerup.NormalState')
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_deactivate_transitions_to_normal_state(self, mock_pygame,
                                                    mock_load_png_sequence,
                                                    mock_normal_state):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.active_powerup = ExpandPowerUp(mock_game, Mock())
        mock_state = Mock()
        mock_normal_state.return_value = mock_state
        mock_game.balls = [Mock(), Mock(), Mock()]
        for ball in mock_game.balls:
            ball.base_speed = 11
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')
        powerup._activate = Mock()

        powerup.update()

        mock_game.paddle.transition.assert_called_once_with(mock_state)
        self.assertEqual(len(mock_game.balls), 3)
        for ball in mock_game.balls:
            self.assertEqual(ball.base_speed, 10)


class TestLaserPowerUp(TestCase):

    @patch('arkanoid.sprites.powerup.LaserState')
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_activate_transitions_to_laser_state(self, mock_pygame,
                                                 mock_load_png_sequence,
                                                 mock_laser_state):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_state = Mock()
        mock_laser_state.return_value = mock_state
        mock_game.balls = [Mock(), Mock(), Mock()]
        for ball in mock_game.balls:
            ball.base_speed = 10
        powerup = LaserPowerUp(mock_game, Mock())

        powerup.update()

        mock_load_png_sequence.assert_called_once_with('powerup_laser')
        mock_game.paddle.transition.assert_called_once_with(mock_state)
        self.assertEqual(len(mock_game.balls), 3)
        for ball in mock_game.balls:
            self.assertEqual(ball.base_speed, 11)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_no_activate_when_already_laser(self, mock_pygame,
                                            mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.active_powerup = LaserPowerUp(mock_game, Mock())
        powerup = LaserPowerUp(mock_game, Mock())
        powerup._activate = Mock()

        powerup.update()

        self.assertEqual(powerup._activate.call_count, 0)

    @patch('arkanoid.sprites.powerup.NormalState')
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_deactivate_transitions_to_normal_state(self, mock_pygame,
                                                    mock_load_png_sequence,
                                                    mock_normal_state):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.active_powerup = LaserPowerUp(mock_game, Mock())
        mock_state = Mock()
        mock_normal_state.return_value = mock_state
        mock_game.balls = [Mock(), Mock(), Mock()]
        for ball in mock_game.balls:
            ball.base_speed = 11
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')
        powerup._activate = Mock()

        powerup.update()

        mock_game.paddle.transition.assert_called_once_with(mock_state)
        self.assertEqual(len(mock_game.balls), 3)
        for ball in mock_game.balls:
            self.assertEqual(ball.base_speed, 10)


class TestCatchPowerUp(TestCase):

    @patch('arkanoid.sprites.powerup.receiver')
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_activate_configures_catch(self, mock_pygame,
                                       mock_load_png_sequence,
                                       mock_receiver):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        powerup = CatchPowerUp(mock_game, Mock())

        powerup.update()

        mock_load_png_sequence.assert_called_once_with('powerup_catch')
        mock_game.paddle.ball_collide_callbacks.append.assert_called_once_with(
            powerup._catch
        )
        mock_receiver.register_handler.assert_called_once_with(
            mock_pygame.KEYUP, powerup._release_ball)

    @patch('arkanoid.sprites.powerup.receiver')
    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_deactivate(self, mock_pygame,
                        mock_load_png_sequence,
                        mock_receiver):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        catch_powerup = CatchPowerUp(mock_game, Mock())
        mock_game.active_powerup = catch_powerup
        mock_game.balls = [Mock(), Mock(), Mock()]
        powerup = PowerUp(mock_game, Mock(), 'test_prefix')
        powerup._activate = Mock()

        powerup.update()

        mock_game.paddle.ball_collide_callbacks.remove.assert_called_once_with(
            catch_powerup._catch
        )
        mock_receiver.unregister_handler.assert_called_once_with(
            catch_powerup._release_ball
        )
        for ball in mock_game.balls:
            ball.release.assert_called_once_with()

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_release_ball(self, mock_pygame, mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.balls = [Mock(), Mock(), Mock()]
        mock_event = Mock()
        mock_event.key = mock_pygame.K_SPACE  # Spacebar event

        catch_powerup = CatchPowerUp(mock_game, Mock())
        catch_powerup._release_ball(mock_event)

        for ball in mock_game.balls:
            ball.release.assert_called_once_with()

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_release_ball_when_other_key_pressed(self, mock_pygame,
                                                 mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_game.balls = [Mock(), Mock(), Mock()]
        mock_event = Mock()
        mock_event.key = mock_pygame.SOME_OTHER_KEY

        catch_powerup = CatchPowerUp(mock_game, Mock())
        catch_powerup._release_ball(mock_event)

        for ball in mock_game.balls:
            self.assertEqual(ball.call_count, 0)

    @patch('arkanoid.sprites.powerup.load_png_sequence')
    @patch('arkanoid.sprites.powerup.pygame')
    def test_catch_anchors_ball(self, mock_pygame,
                                mock_load_png_sequence):
        mock_game = _configure_mocks(mock_load_png_sequence, mock_pygame)
        mock_ball = Mock()
        mock_ball.rect.bottomleft = [10]
        mock_game.paddle.rect.topleft = [5]
        mock_ball.rect.height = 5

        catch_powerup = CatchPowerUp(mock_game, Mock())
        catch_powerup._catch(mock_ball)

        mock_ball.anchor.assert_called_once_with(mock_game.paddle, (5, -5))
