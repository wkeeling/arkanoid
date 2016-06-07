import math
from unittest import TestCase

import pygame

import arkanoid


class TestPaddle(TestCase):

    def test_bounce_strategy(self):
        angles = []
        paddle = pygame.Rect(100, 600, 80, 15)

        for i in range(103, 183, 10):
            ball = pygame.Rect(i, 602, 5, 5)
            angle = arkanoid.Paddle.bounce_strategy(paddle, ball)
            angles.append(math.floor(math.degrees(angle)))

        self.assertTrue(-155 <= angles[0] <= -145)
        self.assertTrue(-135 <= angles[1] <= -125)
        self.assertTrue(-120 <= angles[2] <= -110)
        self.assertTrue(-105 <= angles[3] <= -95)
        self.assertTrue(-85 <= angles[4] <= -75)
        self.assertTrue(-70 <= angles[5] <= -60)
        self.assertTrue(-55 <= angles[6] <= -45)
        self.assertTrue(-35 <= angles[7] <= -25)

