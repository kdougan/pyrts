import pygame
from pygame import Vector2


class Building:
    def __init__(self, pos: Vector2, size: int = 10) -> None:
        self.pos = Vector2(pos)
        self.size = size
        self.spawn_point = self.pos + Vector2(size//2, size)
        self.waypoint = self.spawn_point + Vector2(0, 10)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surf):
        pygame.draw.rect(surf, (200, 0, 0), (self.pos, (self.size, self.size)))
        pygame.draw.rect(surf, (0, 200, 0), (self.spawn_point, (2, 2)))
        pygame.draw.rect(surf, (200, 200, 0), (self.waypoint, (2, 2)))
