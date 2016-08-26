from unittest import TestCase
from unittest.mock import (call,
                           Mock,
                           patch)

from arkanoid.rounds.base import BaseRound


class TestBaseRound(TestCase):

    @patch('arkanoid.rounds.base.pygame')
    def test_sets_brick_in_position_0_0(self, mock_pygame):
        mock_screen = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_edges = Mock()
        mock_edges.left.rect.x = 0
        mock_edges.left.rect.width = 15
        mock_edges.top.rect.y = 150
        mock_edges.top.rect.height = 15
        mock_create_edges = Mock()
        mock_create_edges.return_value = mock_edges
        mock_background = Mock()
        mock_create_background = Mock()
        mock_create_background.return_value = mock_background
        mock_create_bricks = Mock()
        BaseRound._create_edges = mock_create_edges
        BaseRound._create_background = mock_create_background
        BaseRound._create_bricks = mock_create_bricks
        mock_image, mock_rect = Mock(), Mock()
        mock_brick = Mock()
        mock_brick.image = mock_image
        mock_brick.rect = mock_rect
        mock_brick.rect.width = 42
        mock_brick.rect.height = 21

        base_round = BaseRound(top_offset=150)
        base_round._blit_brick(mock_brick, 0, 0)

        mock_screen.blit.assert_has_calls([call(mock_background, (0, 150)),
                                           call(mock_image, (15, 165))])
