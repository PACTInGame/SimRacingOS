import pygame

from SimRacingUI import SimRacingUI
from lfs_interface import LFSInterface


class SimRacingOS:
    def __init__(self):
        self.sim_racing_ui = None
        self.UI = None
        self.running = True
        self.lfs_interface = LFSInterface(self)
        self.wheel_connected = False
        self.retries = 0  # TODO change dummy to actual wheel connection
        self.connect_wheel()
        self.start_lfs()
        self.start_ui()
        self.game_loop()

    def game_loop(self):
        while self.running:
            if self.sim_racing_ui == "stopped":
                self.start_ui()

    def check_wheel_connected(self):
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        return count > 1

    def start_ui(self):
        self.sim_racing_ui = "started"
        self.UI = SimRacingUI(self)
        self.UI.run()

    def connect_wheel(self):
        ui = SimRacingUI(self, "wheel_prompt")
        ui.run()

    def start_lfs(self):
        print("Start LFS")
        self.lfs_interface.start_lfs()
        print("Connect to LFS")
        while not self.lfs_interface.connect_to_lfs():
            pass


if __name__ == "__main__":
    os = SimRacingOS()
