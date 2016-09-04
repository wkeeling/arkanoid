from unittest import TestCase
from unittest.mock import (Mock,
                           patch)

from arkanoid.sprites.powerup import PowerUp


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
