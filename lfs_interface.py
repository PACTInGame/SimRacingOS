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
        self.lfs_connector = LFSConnection(self.os.user_name, self.os.qnummer)
        pyautogui.FAILSAFE = False


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
        self.lfs_connector.obtain_PLID = True
        self.lfs_connector.uebung = uebung
        self.lfs_connector.laps_done = 0
        self.lfs_connector.splittimes = []
        self.lfs_connector.penalty = False
        self.lfs_connector.hit_an_object = False
        self.lfs_connector.crossed_checkpoint1 = False
        self.lfs_connector.crossed_checkpoint2 = False
        self.lfs_connector.crossed_checkpoint3 = False
        self.lfs_connector.came_to_standstill = False
        self.lfs_connector.brake_distances = []
        self.lfs_connector.brake_distance_start = 0
        self.lfs_connector.brake_speed_start = 0
        self.lfs_connector.speeds = []


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
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)
                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter()
                    reason = "Du hast eine Strafe erhalten."
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
            MIN_SPEED = 78 if uebung == "Notbremsung" else 68 # km/h
            FAILURE_DISPLAY_TIME = 5  # seconds

            connector = self.lfs_connector

            checkpoint = 0
            failed = None

            def check_speed():
                if uebung == "Ausweichen":
                    self.lfs_connector.speeds.append(connector.vehicle_model.speed)
                if connector.vehicle_model.speed < MIN_SPEED:
                    return time.perf_counter(), "Du warst nicht schnell genug."
                return None, ""

            while True:
                restart, quit = handle_button_clicks()

                # Process checkpoints and speed checks
                if len(connector.splittimes) == 1 and checkpoint == 0:
                    checkpoint = 1
                    failed, reason = check_speed()
                    print("Checked_Speed_Min")
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)
                    if uebung == "Notbremsung_Ausweichen":
                        MIN_SPEED = 78

                if len(connector.splittimes) == 2 and checkpoint == 1:
                    checkpoint += 1
                    failed, reason = check_speed()

                    if failed is not None:
                        self.os.UI.draw_info_button(reason)
                    if uebung == "Notbremsung_Ausweichen":
                        MIN_SPEED = 88

                if len(connector.splittimes) == 3 and checkpoint == 2:
                    checkpoint += 1
                    failed, reason = check_speed()
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)

                # Check for collisions
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter()
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)

                if connector.crossed_checkpoint2 and not connector.came_to_standstill:
                    failed = time.perf_counter()
                    reason = "Du hast nicht angehalten."
                    self.os.UI.draw_info_button(reason)
                    connector.crossed_checkpoint1 = False
                    connector.crossed_checkpoint2 = False
                    connector.came_to_standstill = False

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter()
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)

                # Check exit conditions
                if (connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    print(connector.laps_done)
                    break

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or connector.laps_done == 1:
                cleanup_and_quit()

        def handle_evade():
            """Handle evasion exercise (Ausweichen)"""
            MIN_SPEED = 68
            FAILURE_DISPLAY_TIME = 5  # seconds

            connector = self.lfs_connector

            checkpoint = 0
            failed = None

            def check_speed():
                connector.speeds.append(connector.vehicle_model.speed)
                if connector.vehicle_model.speed < MIN_SPEED:
                    return time.perf_counter(), "Du warst nicht schnell genug."
                return None, ""

            while True:
                restart, quit = handle_button_clicks()

                # Process checkpoints and speed checks
                if len(connector.splittimes) == 1 and checkpoint == 0:
                    checkpoint = 1
                    failed, reason = check_speed()
                    print("Checked_Speed_Min")
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)


                if len(connector.splittimes) == 2 and checkpoint == 1:
                    checkpoint += 1
                    failed, reason = check_speed()

                    if failed is not None:
                        self.os.UI.draw_info_button(reason)


                if len(connector.splittimes) == 3 and checkpoint == 2:
                    checkpoint += 1
                    failed, reason = check_speed()
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)

                # Check for collisions
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter()
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)


                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter()
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)

                # Check exit conditions
                if (connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    print(connector.laps_done)
                    break

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or connector.laps_done == 1:
                cleanup_and_quit()


        def handle_hotlap():
            """Handle hotlap exercises (HotlapBL1 and HotlapWE2)"""
            while True:
                restart, quit = handle_button_clicks()
                if restart or quit:
                    print("restart or quit")
                    break

            if restart:
                cleanup_and_restart()
            elif quit:
                cleanup_and_quit(True)
        def handle_practice():
            """Handle practice exercises (PracticeBL1 and PracticeWE2)"""
            while True:
                restart, quit = handle_button_clicks()
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
            "Notbremsung_Ausweichen": handle_emergency_brake,
            "Ausweichen": handle_evade,
            "HotlapBL1": handle_hotlap,
            "HotlapWE2": handle_hotlap,
            "PracticeBL1": handle_practice,
            "PracticeWE2": handle_practice,
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
        pyautogui.click(2644, 1267)
        time.sleep(0.5)
        pyautogui.click(3549, 671)
        time.sleep(0.5)
        pyautogui.click(1467, 1233)
        time.sleep(1)

    def start_singleplayer_after_track(self):
        time.sleep(0.3)
        pyautogui.click(2644, 1267)
        time.sleep(0.5)
        pyautogui.click(3549, 671)
        time.sleep(0.2)
