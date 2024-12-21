import pygame
from pynput import keyboard
import threading
from win32gui import SetWindowPos
import config
from race_type_functions import start_hotlap_blackwood


class UIManager:
    def __init__(self, screen, lfs_interface):
        self.listener_thread = None
        self.listener = None
        self.listener_running = None
        self.screen = screen
        self.lfs_interface = lfs_interface
        self.lfs_interface.ui_manager = self
        self.current_screen = "main_menu"
        self.screens = {
            "main_menu": self.draw_main_menu,
            "wheel_prompt": self.draw_wheel_prompt,
            "leaderboard": self.draw_leaderboard,
            "setup_wheel": self.draw_setup_wheel,
            "in_game": self.draw_in_game,
        }
        self.hover_image = pygame.image.load("data/images/selected.png")
        self.hovered_over = None
        self.window_open = True
        self.setup_keyboard_listener()

    def setup_keyboard_listener(self):
        self.listener_running = True
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener_thread = threading.Thread(target=self.listen_for_keypress)
        self.listener_thread.start()

    def on_press(self, key):
        try:
            if key.char == 'z':
                print("The 'z' key was pressed.")
                self.current_screen = "main_menu"
                self.stop_listener()

        except AttributeError:
            pass

    def on_release(self, key):
        pass

    def listen_for_keypress(self):
        with self.listener as listener:
            while self.listener_running:
                listener.wait()
            listener.stop()

    def stop_listener(self):
        self.listener.stop()
        self.listener_running = False
        self.listener_thread.join()

    def restart_window(self):
        print("Restarting window")
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.NOFRAME)
        self.window_open = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.check_mouse_position(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.check_button_clicks(event.pos)

    def update(self):
        pass

    def draw(self):
        self.screen.fill((1, 255, 0))
        self.screens[self.current_screen]()

    def draw_in_game(self):

    # TODO make transparent window in game and do not close the window
    def draw_setup_wheel(self):
        bg = pygame.image.load("data/images/setup_wheel.png")
        self.screen.blit(bg, (0, 0))

    def draw_main_menu(self):
        # Draw main menu UI elements
        bg = pygame.image.load("data/images/background_test.png")
        self.screen.blit(bg, (0, 0))
        if self.hovered_over:
            self.draw_hover_image(self.hovered_over)

    def draw_hover_image(self, pos):
        self.screen.blit(self.hover_image, pos)

    def draw_wheel_prompt(self):
        # Draw wheel prompt UI elements
        pass

    def draw_leaderboard(self):
        # Draw leaderboard UI elements
        pass

    def close_screen(self):
        self.running = False
        pygame.display.quit()
        pygame.quit()

    def find_buttons_ui(self, mouse_pos):
        if self.current_screen == "main_menu":
            pos = list(self.get_functions().keys())
            for i in range(len(pos)):
                if pos[i][0] < mouse_pos[0] < pos[i][0] + 208 and pos[i][1] < mouse_pos[1] < pos[i][1] + 208:
                    return pos[i]
            return None

    def get_functions(self):
        functions = {
            (84, 94): "start_hotlap_bl",
            (517, 94): "b1_training",
            (954, 94): "b2_training",
            (1390, 94): "notbremsung_ausweichen",
        }
        return functions

    def check_button_function(self, position):
        functions = self.get_functions()
        functionality = functions.get(position)
        print(functionality)
        actions = {
            "start_hotlap_bl": start_hotlap_blackwood,
        }
        actions[functionality](self)
        self.setup_keyboard_listener()

    def check_button_clicks(self, mouse_pos):
        # Check if any buttons were clicked and change screens accordingly
        position = self.find_buttons_ui(mouse_pos)
        if position is not None:
            print("Check button Click")
            self.check_button_function(position)

    def check_mouse_position(self, mouse_pos):
        position = self.find_buttons_ui(mouse_pos)
        self.hovered_over = position
