import pygame
from pygame import Vector2
from typing import Tuple
pygame.init()
scale = 3
screen_size = Vector2(240, 240)
scr = pygame.Surface(screen_size)
win = pygame.display.set_mode(
    list(map(int, screen_size*scale)))
scr.convert_alpha()
clock = pygame.time.Clock()


def draw_circle(surface: pygame.Surface, color: Tuple[int, int, int, int], pos: Vector2, radius: int, line_width: int = 0) -> None:
    size = Vector2(radius*2, radius*2)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(surf, color, size/2, radius, line_width)
    surface.blit(surf, pos - size/2)


while 1:
    dt = clock.tick(60)/1000
    for e in pygame.event.get():
        if (e.type == pygame.QUIT or
            (e.type == pygame.KEYDOWN and
             e.key == pygame.K_ESCAPE)):
            exit()
    scr.fill((0, 0, 0))
    pygame.draw.circle(scr, (255, 255, 255), (80, 120), 20)
    draw_circle(scr, (255, 255, 255, 100), (160, 120), 20)
    pygame.transform.scale(scr, win.get_size(), win)
    pygame.display.flip()
