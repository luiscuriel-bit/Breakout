import random
from typing import TypeVar

from gale.factory import Factory

import settings
from src.powerups.PowerUp import PowerUp


class Multiplier2x(PowerUp):

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, 6)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        settings.SOUNDS["paddle_hit"].stop()
        settings.SOUNDS["paddle_hit"].play()
        play_state.multiplier2x = True
        self.in_play = False
