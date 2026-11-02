import pygame

from . import settings as S


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(S.TITLE)
        self.screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT), pygame.SCALED)
        self.clock = pygame.time.Clock()
        pygame.key.set_repeat(400, 35)
        self.running = True

        from .scenes.menu import MainMenu
        self.scene = MainMenu(self)

    def change(self, scene):
        self.scene = scene

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = min(self.clock.tick(S.FPS) / 1000, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(event)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
