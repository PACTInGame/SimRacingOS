import threading
import pygame
import win32gui
from pynput import keyboard

import config
import pyinsim
from race_type_functions import start_hotlap_blackwood, start_b1_lenken, start_b1_notbremsung, \
    start_b1_notbremsung_ausweichen, start_b1_ausweichen


class SimRacingUI:
    def __init__(self, os, current_screen="main_menu"):
        self.os = os
        pygame.init()
        self.running = True
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.NOFRAME)
        hwnd = pygame.display.get_wm_info()['window']
        win32gui.SetForegroundWindow(hwnd)
        self.current_screen = current_screen
        self.hover_image = pygame.image.load("data/images/selected.png")
        self.hovered_over = None
        self.listener = None
        self.listener_thread = None

    def draw(self):
        if self.current_screen == "main_menu":
            self.draw_main_menu()
        elif self.current_screen == "wheel_prompt":
            self.draw_wheel_prompt()
        elif self.current_screen == "b1_selection":
            self.draw_b1_selection()

    def draw_b1_selection(self):
        bg = pygame.image.load("data/images/b1.png")
        self.screen.blit(bg, (0, 0))

    def draw_wheel_prompt(self):
        bg = pygame.image.load("data/images/setup_wheel.png")
        self.screen.blit(bg, (0, 0))

    def draw_explanation(self, name):
        bg = pygame.image.load(f"data/images/{name}.png")
        self.screen.blit(bg, (0, 0))

    def draw_main_menu(self):
        bg = pygame.image.load("data/images/background_test.png")
        self.screen.blit(bg, (0, 0))
        if self.hovered_over:
            self.screen.blit(self.hover_image, self.hovered_over)

    def draw_buttons(self):
        self.os.lfs_interface.lfs_connector.send_button(
            1, pyinsim.ISB_DARK | pyinsim.ISB_CLICK, 100, 0, 25, 10, "Restart Task"
        )
        self.os.lfs_interface.lfs_connector.send_button(
            2, pyinsim.ISB_DARK | pyinsim.ISB_CLICK, 110, 0, 25, 10, "Back to Menu"
        )

    def draw_info_button(self, text):
        self.os.lfs_interface.lfs_connector.send_button(
            3, pyinsim.ISB_DARK, 80, 50, 100, 20, text
        )

    def del_info_button(self):
        self.os.lfs_interface.lfs_connector.del_button(3)

    def stop_listener(self):
        if self.listener:
            self.listener.stop()
            self.listener_thread.join()
            self.listener = None
            self.listener_thread = None

    def get_functions_main_menu(self):
        return {
            (84, 94): "start_hotlap_bl",
            (517, 94): "b1_training",
            (954, 94): "b2_training",
            (1390, 94): "notbremsung_ausweichen",
        }

    def get_functions_b1_training(self):
        return {
            (86, 72): "Lenkradhaltung",
            (145, 238): "Notbremsung",
            (216, 410): "Notbremsung_Ausweichen",
            (286, 580): "Ausweichen",
            (355, 735): "Untersteuern",
            (418, 900): "Übersteuern",
        }

    def check_button_function(self, position):
        if self.current_screen == "main_menu":
            functions = self.get_functions_main_menu()
            functionality = functions.get(position)
            if functionality == "start_hotlap_bl":
                start_hotlap_blackwood(self)
            if functionality == "b1_training":
                self.current_screen = "b1_selection"
        elif self.current_screen == "b1_selection":
            functions = self.get_functions_b1_training()
            functionality = functions.get(position)
            if functionality == "Lenkradhaltung":
                start_b1_lenken(self)
            elif functionality == "Notbremsung":
                start_b1_notbremsung(self)
            elif functionality == "Notbremsung_Ausweichen":
                start_b1_notbremsung_ausweichen(self)
            elif functionality == "Ausweichen":
                start_b1_ausweichen(self)

    def find_buttons_ui(self, mouse_pos):
        if self.current_screen == "main_menu":
            for pos, _ in self.get_functions_main_menu().items():
                if pos[0] < mouse_pos[0] < pos[0] + 208 and pos[1] < mouse_pos[1] < pos[1] + 208:
                    return pos
        elif self.current_screen == "b1_selection":
            for pos, _ in self.get_functions_b1_training().items():
                if pos[0] < mouse_pos[0] < pos[0] + 1450 and pos[1] < mouse_pos[1] < pos[1] + 96:
                    print("looking for UI")
                    return pos
        return None

    def check_button_clicks(self, mouse_pos):
        position = self.find_buttons_ui(mouse_pos)
        if position:
            self.check_button_function(position)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEMOTION:
                self.hovered_over = self.find_buttons_ui(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.check_button_clicks(event.pos)

    def close_screen(self):
        self.running = False
        pygame.display.quit()

    def run(self):
        while self.running:
            self.draw()
            pygame.display.flip()
            self.handle_events()

            self.clock.tick(30)
            if self.current_screen == "wheel_prompt":
                if self.os.check_wheel_connected():
                    self.running = False

        pygame.quit()

# if __name__ == '__main__':
# SimRacingUI().run()
