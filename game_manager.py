import pygame
import win32gui
from win32gui import SetWindowPos
from ui_manager import UIManager
from lfs_interface import LFSInterface
import config


class GameManager:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.NOFRAME)
        self.lfs_interface = LFSInterface()
        self.ui_manager = UIManager(self.screen, self.lfs_interface)
        self.running = True

    def run(self):
        self.start_lfs()
        self.setup_window()

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def start_lfs(self):
        print("Start LFS")
        self.lfs_interface.start_lfs()
        print("Connect to LFS")
        while not self.lfs_interface.connect_to_lfs():
            pass

    def setup_window(self):
        print("WINDOW to Front")
        hwnd = pygame.display.get_wm_info()['window']
        win32gui.SetForegroundWindow(hwnd)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            self.ui_manager.handle_event(event)

    def update(self):
        self.ui_manager.update()
        self.lfs_interface.update()

    def draw(self):
        if self.ui_manager.window_open:
            self.ui_manager.draw()
            pygame.display.flip()
