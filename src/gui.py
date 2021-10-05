import pygame_gui
import pygame
from pygame import Vector2
from pygame import Rect


class GUI:
    def __init__(self, game):
        self.game = game
        self.manager = pygame_gui.UIManager(self.game.win.get_size())
        self.create_ui()

    def create_ui(self):
        self.show_health_button = pygame_gui.elements.UIButton(
            relative_rect=Rect(Vector2(10, 10), Vector2(100, 20)),
            text='+ Health' if not self.game.options.show_health else '- Health',
            manager=self.manager
        )
        self.show_perception_button = pygame_gui.elements.UIButton(
            relative_rect=Rect(Vector2(10, 40), Vector2(100, 20)),
            text='+ Percep' if not self.game.options.show_perception else '- Percep',
            manager=self.manager
        )

    def update(self, dt):
        self.manager.update(dt)

    def process_events(self, event):
        if (
            event.type == pygame.USEREVENT
            and event.user_type == pygame_gui.UI_BUTTON_PRESSED
        ):
            if event.ui_element == self.show_health_button:
                self.game.options.show_health = not self.game.options.show_health
                self.show_health_button.set_text(
                    '+ Health' if not self.game.options.show_health else '- Health')
            elif event.ui_element == self.show_perception_button:
                self.game.options.show_perception = not self.game.options.show_perception
                self.show_perception_button.set_text(
                    '+ Percep' if not self.game.options.show_perception else '- Percep')

        self.manager.process_events(event)

    def draw(self):
        self.manager.draw_ui(self.game.win)
