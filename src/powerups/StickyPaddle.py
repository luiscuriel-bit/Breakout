import random
from typing import TypeVar

from gale.factory import Factory

import settings
from src.Ball import Ball
from src.powerups.PowerUp import PowerUp


class StickyPaddle(PowerUp):

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, 3)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        settings.SOUNDS["paddle_hit"].stop()
        settings.SOUNDS["paddle_hit"].play()
        play_state.sticky = True
        self.in_play = False
