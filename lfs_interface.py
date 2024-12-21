import os
import subprocess
import threading
import time
import psutil
import config
from LfsConnector import LFSConnection
import pyautogui


class LFSInterface:
    def __init__(self, os):
        self.os = os
        self.ui_manager = None
        self.lfs_process = None
        self.lfs_is_running = False
        self.lfs_connector = LFSConnection()

    def start_lfs(self):
        self.lfs_process = subprocess.Popen(config.LFS_PATH, cwd=os.path.dirname(config.LFS_PATH))

    def connect_to_lfs(self):
        time.sleep(1)
        retries = 0
        print("Check if LFS is running")
        while not self.is_lfs_running():
            time.sleep(1)
            if retries == 5:
                self.start_lfs()
            if retries > 10:
                return False
            retries += 1

        time.sleep(1)
        print("Connecting to LFS.")
        thread = threading.Thread(target=self.lfs_connector.run)
        thread.start()

        retries = 0
        while self.lfs_connector.insim is None:
            time.sleep(1)
        while not self.lfs_connector.is_connected:
            self.lfs_connector.ping_insim()
            time.sleep(1)
            retries += 1
            if retries > 10:
                self.lfs_connector.stop()
                return False

        print("Connected to LFS.")
        time.sleep(0.1)
        self.start_singleplayer()
        return True

    def track_uebung(self, uebung):
        """
        Track and manage different driving exercises.

        Args:
            uebung: Name of the exercise to run
        """
        self.lfs_connector.uebung = uebung

        def handle_button_clicks():
            """Check and handle button clicks, returning whether restart or quit was requested"""
            clicked = self.lfs_connector.buttons_clicked
            restart_requested = 1 in clicked
            quit_requested = 2 in clicked

            if restart_requested:
                self.lfs_connector.buttons_clicked.remove(1)
            if quit_requested:
                self.lfs_connector.buttons_clicked.remove(2)

            return restart_requested, quit_requested

        def cleanup_and_quit(hotlap=False):
            """Perform cleanup actions when quitting exercise"""
            self.os.lfs_interface.lfs_connector.del_button(1)
            self.os.lfs_interface.lfs_connector.del_button(2)
            self.os.lfs_interface.lfs_connector.del_button(3)
            self.os.lfs_interface.lfs_connector.laps_done = 0
            self.os.lfs_interface.lfs_connector.hit_an_object = False

            if not hotlap:
                self.send_commands_to_lfs([b"/shift x"])
            else:
                self.send_commands_to_lfs([b"/entry"])

            while self.lfs_connector.on_track:
                pass
            if hotlap:
                self.start_singleplayer_after_track()
            self.os.lfs_interface.lfs_connector.splittimes = []
            self.os.sim_racing_ui = "stopped"
            self.os.UI.stop_listener()

        def cleanup_and_restart():
            self.lfs_connector.del_button(3)
            self.lfs_connector.laps_done = 0
            self.lfs_connector.hit_an_object = False
            self.lfs_connector.splittimes = []
            time.sleep(0.5)
            self.send_commands_to_lfs([b"/restart"])
            self.track_uebung(uebung)

        def handle_steering_wheel():
            """Handle the steering wheel exercise (Lenkradhaltung)"""
            failed = None
            FAILURE_DISPLAY_TIME = 3  # seconds
            reason = ""
            while True:

                restart, quit = handle_button_clicks()
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter()
                    reason = "You hit an Object"
                    self.os.UI.draw_info_button(reason)

                if (self.lfs_connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    break
            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or self.lfs_connector.laps_done == 1:
                cleanup_and_quit()

        def handle_emergency_brake():
            """Handle the emergency brake exercise (Notbremsung)"""
            MIN_SPEED = 78  # km/h
            FAILURE_DISPLAY_TIME = 3  # seconds

            connector = self.os.lfs_interface.lfs_connector
            connector.splittimes = []
            checkpoint = 0
            failed = None

            def check_speed():
                print(connector.vehicle_model.speed)
                if connector.vehicle_model.speed < MIN_SPEED:
                    return time.perf_counter(), "You were too slow"
                return None, ""

            while True:
                restart, quit = handle_button_clicks()

                # Process checkpoints and speed checks
                if len(connector.splittimes) == 1 and checkpoint == 0:
                    checkpoint = 1
                    failed, reason = check_speed()
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)

                if len(connector.splittimes) == 2 and checkpoint in (1, 2):
                    checkpoint += 1
                    failed, reason = check_speed()
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)

                # Check for collisions
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter()
                    reason = "You hit an Object"
                    self.os.UI.draw_info_button(reason)

                # Display failure message
                # TODO check standstill
                # Check exit conditions
                if (connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    break

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or connector.laps_done == 1:
                cleanup_and_quit()

        def handle_hotlap():
            """Handle hotlap exercises (HotlapBL1 and HotlapWE2)"""
            while True:
                restart, quit = handle_button_clicks()
                # print("hotlapping")
                if restart or quit:
                    print("restart or quit")
                    break

            if restart:
                cleanup_and_restart()
            elif quit:
                cleanup_and_quit(True)

        # Map exercise names to their handler functions
        exercise_handlers = {
            "Lenkradhaltung": handle_steering_wheel,
            "Notbremsung": handle_emergency_brake,
            "HotlapBL1": handle_hotlap,
            "HotlapWE2": handle_hotlap
        }

        # Run the appropriate exercise handler
        if handler := exercise_handlers.get(uebung):
            handler()

    def is_lfs_running(self):
        for proc in psutil.process_iter():
            try:
                if proc.name() == "LFS.exe":
                    print("LFS.exe seems to be running. Starting!")
                    return True
            except psutil.AccessDenied:
                print("Insufficient permissions to check for System Apps.")
                return True
        return False

    def get_lfs_data(self):
        pass

    def send_commands_to_lfs(self, commands):
        for command in commands:
            self.lfs_connector.send_message(command)

    def update(self):
        pass

    def start_singleplayer(self):
        time.sleep(0.3)
        pyautogui.click(947, 1073)
        time.sleep(0.5)
        pyautogui.click(1659, 561)
        time.sleep(0.5)
        pyautogui.click(92, 1053)
        time.sleep(1)

    def start_singleplayer_after_track(self):
        time.sleep(0.3)
        pyautogui.click(947, 1073)
        time.sleep(0.5)
        pyautogui.click(1659, 561)
        time.sleep(0.2)
