import math
from unittest import TestCase

import pygame

import arkanoid


class TestPaddle(TestCase):

    def test_bounce_strategy(self):
        angles = []
        paddle = pygame.Rect(100, 600, 60, 15)

        for i in range(103, 163, 10):
            ball = pygame.Rect(i, 602, 5, 5)
            angle = arkanoid.Paddle.bounce_strategy(paddle, ball)
            angles.append(int(math.degrees(angle)))

        self.assertTrue(angles[0], -130)
        self.assertTrue(angles[1], -115)
        self.assertTrue(angles[2], -100)
        self.assertTrue(angles[3], -80)
        self.assertTrue(angles[4], -65)
        self.assertTrue(angles[5], -50)

