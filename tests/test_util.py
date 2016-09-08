import os
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from arkanoid.utils.util import (h_centre_pos,
                                 save_high_score,
                                 load_high_score)


class TestUtil(TestCase):

    def setUp(self):
        self._high_score_file = os.path.join(os.path.expanduser('~'),
                                             '.arkanoid')
        self._high_score_file_backup = os.path.join(os.path.expanduser('~'),
                                                    '.arkanoid.bak')
        if os.path.exists(self._high_score_file):
            os.rename(self._high_score_file, self._high_score_file_backup)

    def tearDown(self):
        if os.path.exists(self._high_score_file_backup):
            os.rename(self._high_score_file_backup, self._high_score_file)

    @patch('arkanoid.utils.util.pygame')
    def test_returns_left_pos_for_horizontal_centre(self, mock_pygame):
        mock_screen = Mock()
        mock_screen.get_width.return_value = 600
        mock_pygame.display.get_surface.return_value = mock_screen

        mock_surface = Mock()
        mock_surface.get_width.return_value = 100

        self.assertEqual(h_centre_pos(mock_surface), 250)

    def test_saves_high_score(self):
        high_score = 1000
        save_high_score(high_score)

        with open(self._high_score_file) as file:
            saved_score = int(file.read().strip())
            self.assertEqual(saved_score, high_score)

    def test_loads_high_score_when_file_exists(self):
        high_score = 2000

        with open(self._high_score_file, 'w') as file:
            file.write(str(high_score))

        self.assertEqual(load_high_score(), high_score)

    def test_loads_high_score_when_file_not_exists(self):
        try:
            os.remove(self._high_score_file)
        except OSError:
            pass

        self.assertEqual(load_high_score(), 0)
