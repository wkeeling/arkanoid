from unittest.mock import Mock
from unittest.mock import patch
from unittest import TestCase

from arkanoid.utils import h_centre_pos


class TestUtils(TestCase):

    @patch('arkanoid.utils.pygame')
    def test_returns_left_pos_for_horizontal_centre(self, mock_pygame):
        mock_screen = Mock()
        mock_screen.get_width.return_value = 600
        mock_pygame.display.get_surface.return_value = mock_screen

        mock_surface = Mock()
        mock_surface.get_width.return_value = 100

        self.assertEqual(h_centre_pos(mock_surface), 250)
