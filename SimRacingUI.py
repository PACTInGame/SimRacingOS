import os
import threading

import keyboard
import pygame
import win32gui
import config
import pyinsim
from login_screen import login_window
from race_type_functions import start_hotlap_blackwood, start_hotlap_westhill, start_practice_westhill, \
    start_practice_blackwood, start_driften, start_b1_uebung, start_freies_ueben, start_b2_uebung


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
        self.current_explain = ""
        self.ready_for_start = ""
        self.starting_count = 0

    def draw(self):
        if self.current_screen == "main_menu":
            self.draw_main_menu()
        elif self.current_screen == "wheel_prompt":
            self.draw_wheel_prompt()
        elif self.current_screen == "b1_selection":
            self.draw_b1_selection()
        elif self.current_screen == "b2_selection":
            self.draw_b2_selection()
        elif self.current_screen == "explain_b1" or self.current_screen == "explain_b2":
            self.draw_explanation()
        elif self.current_screen == "shutdown":
            self.draw_shutdown()
        elif self.current_screen == "starting":
            self.draw_starting()

    def draw_shutdown(self):
        bg = pygame.image.load("data/images/shutdown.png")
        self.screen.blit(bg, (0, 0))

    def draw_b1_selection(self):
        bg = pygame.image.load("data/images/b1_list.png")
        self.screen.blit(bg, (0, 0))

    def draw_b2_selection(self):
        bg = pygame.image.load("data/images/b2_list.png")
        self.screen.blit(bg, (0, 0))

    def draw_wheel_prompt(self):
        bg = pygame.image.load("data/images/Lenkrad.png")
        self.screen.blit(bg, (0, 0))

    def draw_explanation(self):
        bg = pygame.image.load(f"data/images/{self.current_explain}.png")
        self.screen.blit(bg, (0, 0))

    def draw_starting(self):
        if self.starting_count == 0:
            bg = pygame.image.load(f"data/images/starting.png")
        elif self.starting_count == 1:
            bg = pygame.image.load(f"data/images/loading1.png")
        elif self.starting_count == 2:
            bg = pygame.image.load(f"data/images/loading2.png")
        elif self.starting_count == 3:
            bg = pygame.image.load(f"data/images/loading3.png")
        elif self.starting_count == 4:
            bg = pygame.image.load(f"data/images/loading4.png")
        elif self.starting_count == 5:
            bg = pygame.image.load(f"data/images/loading5.png")

        self.screen.blit(bg, (0, 0))

    def draw_main_menu(self):
        bg = pygame.image.load("data/images/Main_Auswahl.png")
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

    def change_user(self):
        self.close_screen()
        self.os.user_name, self.os.qnummer = login_window()
        self.os.lfs_interface.lfs_connector.username = self.os.user_name
        self.os.lfs_interface.lfs_connector.qnummer = self.os.qnummer
        print(f"Logged in as: {self.os.user_name, self.os.qnummer}")
        self.os.sim_racing_ui = "stopped"

    def get_functions_main_menu(self):
        return {
            (136, 586): "start_hotlap_bl",
            (845, 586): "start_hotlap_we",
            (1574, 586): "b1_training",
            (1574, 1115): "b2_training",
            (2307, 586): "driften",
            (4438, 586): "freies_ueben",
            (136, 1115): "start_practice_bl",
            (845, 1115): "start_practice_we",
            (3650, 150): "change_user",
            (4419, 150): "shutdown"

        }

    def get_functions_b1_training(self):
        return {
            (194, 155): "Lenkradhaltung",
            (194, 305): "Zielbremsung",
            (194, 460): "Notbremsung",
            (194, 613): "Notbremsung_Ausweichen",
            (194, 765): "Ausweichen",
            (194, 915): "untersteuern",
            (194, 1065): "uebersteuern",
            (194, 1219): "Schnelles_Ausweichen",
            (40, 26): "back_to_menu"

        }

    def get_functions_b2_training(self):
        return {
            (194, 155): "Notbremsung_Kurve",
            (194, 305): "Doppelspurwechsel",
            (194, 460): "Halbkreis_drift",
            (194, 613): "Ideal_Sicherheitslinie",
            (194, 765): "Rennrunde_fahren",
            (194, 915): "Notbremsung_220",
            (40, 26): "back_to_menu"
        }

    def check_button_function(self, position):
        print(self.current_screen)
        print(self.current_explain)
        print("\n")
        if self.current_screen == "main_menu":
            functions = self.get_functions_main_menu()
            functionality = functions.get(position)
            if functionality == "start_hotlap_bl":
                self.starting_count = 0
                self.current_screen = "starting"
                self.draw_starting()
                start_hotlap_blackwood(self)
            elif functionality == "b1_training":
                self.current_screen = "b1_selection"

            elif functionality == "b2_training":
                self.current_screen = "b2_selection"

            elif functionality == "start_hotlap_we":
                self.starting_count = 0
                self.current_screen = "starting"
                self.draw_starting()
                start_hotlap_westhill(self)
            elif functionality == "start_practice_bl":
                self.starting_count = 0
                self.current_screen = "starting"
                self.draw_starting()
                start_practice_blackwood(self)
            elif functionality == "start_practice_we":
                self.starting_count = 0
                self.current_screen = "starting"
                self.draw_starting()
                start_practice_westhill(self)
            elif functionality == "driften":
                self.starting_count = 0
                self.current_screen = "starting"
                self.draw_starting()
                start_driften(self)
            elif functionality == "freies_ueben":
                self.starting_count = 0
                self.current_screen = "starting"
                self.draw_starting()
                start_freies_ueben(self)
            elif functionality == "change_user":
                self.change_user()
            elif functionality == "shutdown":
                self.current_screen = "shutdown"
                os.system("shutdown /s /f /t 20")


        elif self.current_screen == "b1_selection" or self.current_screen == "explain_b1":
            functions = self.get_functions_b1_training()
            functionality = functions.get(position)
            self.current_explain = functionality
            self.current_screen = "explain_b1"
            if functionality == "back_to_menu":
                self.current_screen = "main_menu"



        elif self.current_screen == "b2_selection" or self.current_screen == "explain_b2":
            functions = self.get_functions_b2_training()
            functionality = functions.get(position)
            self.current_explain = functionality
            self.current_screen = "explain_b2"
            if functionality == "back_to_menu":
                self.current_screen = "main_menu"


    def find_buttons_ui(self, mouse_pos):
        if self.current_screen == "main_menu":
            for pos, _ in self.get_functions_main_menu().items():
                if pos[0] < mouse_pos[0] < pos[0] + 574 and pos[1] < mouse_pos[1] < pos[1] + 68:
                    return pos
        elif self.current_screen == "b1_selection" or self.current_screen == "explain_b1":
            for pos, _ in self.get_functions_b1_training().items():
                if pos[0] < mouse_pos[0] < pos[0] + 2261 and pos[1] < mouse_pos[1] < pos[1] + 115:
                    return pos
        elif self.current_screen == "b2_selection" or self.current_screen == "explain_b2":
            for pos, _ in self.get_functions_b1_training().items():
                if pos[0] < mouse_pos[0] < pos[0] + 2261 and pos[1] < mouse_pos[1] < pos[1] + 115:
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
        if self.ready_for_start != "":
            uebung = self.ready_for_start
            self.ready_for_start = ""
            self.draw_buttons()
            self.os.lfs_interface.track_uebung(uebung)

    def run(self):
        while self.running:
            self.draw()
            pygame.display.flip()
            self.handle_events()

            self.clock.tick(30)
            if self.current_screen == "wheel_prompt":
                if self.os.check_wheel_connected():
                    self.running = False
            elif self.current_screen == "explain_b1" or self.current_screen == "explain_b2":
                if keyboard.is_pressed("enter"):
                    self.current_screen = "starting"
                    self.starting_count = 0
                    if self.current_explain not in ["Notbremsung_Kurve", "Doppelspurwechsel", "Halbkreis_drift", "Ideal_Sicherheitslinie", "Rennrunde_fahren", "Notbremsung_220"]:
                        thread = threading.Thread(target=start_b1_uebung, args=(self, self.current_explain))
                        thread.start()
                    else:
                        thread = threading.Thread(target=start_b2_uebung, args=(self, self.current_explain))
                        thread.start()
            if self.ready_for_start != "":
                self.close_screen()

        pygame.quit()

# if __name__ == '__main__':
# SimRacingUI().run()
