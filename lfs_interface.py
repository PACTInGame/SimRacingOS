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
        self.lfs_connector = LFSConnection(self.os.user_name, self.os.qnummer, self.os)
        pyautogui.FAILSAFE = False
        self.switched_to_menu = False
        self.abs_run = True


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
        self.lfs_connector.drift_values = []
        self.lfs_connector.braking_possible = False
        self.switched_to_menu = False
        self.lfs_connector.failed_brake = False
        self.lfs_connector.y_at_stop = -1


        def handle_button_clicks():
            """Check and handle button clicks, returning whether restart or quit was requested"""
            clicked = self.lfs_connector.buttons_clicked
            restart_requested = 1 in clicked
            quit_requested = 2 in clicked

            if restart_requested:
                self.lfs_connector.buttons_clicked.remove(1)
            if quit_requested:
                self.lfs_connector.buttons_clicked.remove(2)
            if not quit_requested:
                if self.switched_to_menu:
                    quit_requested = True
                    self.switched_to_menu = False
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
            FAILURE_DISPLAY_TIME = 2  # seconds
            reason = ""
            while True:

                restart, quit = handle_button_clicks()
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)
                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)
                if (self.lfs_connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    break
                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or self.lfs_connector.laps_done == 1:
                cleanup_and_quit()

        def handle_emergency_brake():
            """Handle the emergency brake exercise (Notbremsung)"""
            if uebung == "Notbremsung":
                MIN_SPEED = 75
            elif uebung == "Notbremsung_Ausweichen":
                MIN_SPEED = 65
            else:
                MIN_SPEED = 115

            FAILURE_DISPLAY_TIME = 2  # seconds

            connector = self.lfs_connector

            checkpoint = 0
            failed = None

            def check_speed():
                print(connector.vehicle_model.speed)
                print("MIN", MIN_SPEED)
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
                        MIN_SPEED = 75

                if len(connector.splittimes) == 2 and checkpoint == 1:
                    checkpoint += 1
                    failed, reason = check_speed()

                    if failed is not None:
                        self.os.UI.draw_info_button(reason)
                    if uebung == "Notbremsung_Ausweichen":
                        MIN_SPEED = 85

                if len(connector.splittimes) == 3 and checkpoint == 2:
                    checkpoint += 1
                    failed, reason = check_speed()
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)

                # Check for collisions
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)

                if connector.crossed_checkpoint2 and not connector.came_to_standstill:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast nicht angehalten."
                    self.os.UI.draw_info_button(reason)
                    connector.crossed_checkpoint1 = False
                    connector.crossed_checkpoint2 = False
                    connector.came_to_standstill = False

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)

                # Check exit conditions
                if (connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    print(connector.laps_done)
                    break
                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or connector.laps_done == 1:
                cleanup_and_quit()

        def handle_zielbremsung():
            """Handle the zielbremsung exercise """
            MIN_SPEED = 75
            FAILURE_DISPLAY_TIME = 2  # seconds
            connector = self.lfs_connector
            checkpoint = 0
            failed = None

            def check_speed():
                if connector.vehicle_model.speed < MIN_SPEED:
                    return time.perf_counter(), "Du warst nicht schnell genug."
                return None, ""

            while True:
                restart, quit = handle_button_clicks()

                # Process checkpoints and speed checks
                if len(connector.splittimes) == 1 and checkpoint == 0:
                    checkpoint = 1
                    failed, reason = check_speed()
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
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)

                if connector.crossed_checkpoint2 and not connector.came_to_standstill:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast nicht angehalten."
                    self.os.UI.draw_info_button(reason)
                    connector.crossed_checkpoint1 = False
                    connector.crossed_checkpoint2 = False
                    connector.came_to_standstill = False

                if self.lfs_connector.came_to_standstill and self.lfs_connector.distance_to_goal > 8.5:
                    print("DISTANCE,", self.lfs_connector.distance_to_goal)
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du stehst zu weit weg."
                    self.os.UI.draw_info_button(reason)
                    connector.crossed_checkpoint1 = False
                    connector.crossed_checkpoint2 = False
                    connector.came_to_standstill = False

                if self.lfs_connector.came_to_standstill and self.lfs_connector.y_at_stop > 175 * 65536:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du bist zu weit gefahren."
                    self.os.UI.draw_info_button(reason)
                    connector.crossed_checkpoint1 = False
                    connector.crossed_checkpoint2 = False
                    connector.came_to_standstill = False

                if self.lfs_connector.came_to_standstill and not self.lfs_connector.full_brake_pedal:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Das war keine Vollbremsung."
                    self.os.UI.draw_info_button(reason)
                    connector.crossed_checkpoint1 = False
                    connector.crossed_checkpoint2 = False
                    connector.came_to_standstill = False

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)

                # Check exit conditions
                if (connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    print(connector.laps_done)
                    break
                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or connector.laps_done == 1:
                cleanup_and_quit()

        def handle_evade():
            """Handle evasion exercise (Ausweichen)"""
            MIN_SPEED = 65
            FAILURE_DISPLAY_TIME = 2  # seconds

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
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)

                # Check exit conditions
                if (connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    print(connector.laps_done)
                    break
                time.sleep(0.1)

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
                time.sleep(0.2)

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
                time.sleep(0.2)

            if restart:
                cleanup_and_restart()
            elif quit:
                cleanup_and_quit()

        def handle_driften():
            """Handle driften exercise"""

            def circular_difference(a, b, max_value=65536):
                """
                Calculate the circular difference between two numbers in a range of 0 to max_value.

                Parameters:
                    a (int): The first number.
                    b (int): The second number.
                    max_value (int): The maximum value of the range (default is 65536).

                Returns:
                    int: The circular difference between a and b.
                """
                # Ensure both numbers are within the range
                a %= max_value
                b %= max_value

                # Calculate the circular difference
                diff = abs(a - b)
                return min(diff, max_value - diff) / 182.04

            understeering_l = False
            understeering_r = False
            understeering = False
            understeering_timer = time.perf_counter()
            understeering_count = 0
            failed = None
            FAILURE_DISPLAY_TIME = 2  # seconds

            uebersteuern = False
            uebersteuern_timer = time.perf_counter()
            uebersteuern_count = 0
            uebersteuern_max_angle = 0
            uebersteuern_data = []
            avg_speed = [0, 0]
            while True:
                brake = self.lfs_connector.vehicle_model.brake
                heading = self.lfs_connector.vehicle_model.heading
                direction = self.lfs_connector.vehicle_model.direction
                if circular_difference(heading,
                                       direction) > 10 and self.lfs_connector.vehicle_model.speed > 15 and not uebersteuern:

                    uebersteuern = True
                    uebersteuern_timer = time.perf_counter()

                elif circular_difference(heading, direction) < 10 and uebersteuern:
                    print("Oversteering end")
                    uebersteuern = False
                    uebersteuern_time = time.perf_counter() - uebersteuern_timer
                    print(avg_speed)
                    uebersteuern_distance = uebersteuern_time * 0.277 * (avg_speed[0] / avg_speed[1])
                    print(uebersteuern_distance, uebersteuern_time)
                    avg_speed = [0, 0]
                    if 1 < uebersteuern_time < 5 < uebersteuern_distance:
                        uebersteuern_count += 1
                        print("Oversteering for: ", uebersteuern_time, "Distance: ", uebersteuern_distance)
                        uebersteuern_data.append([uebersteuern_time, uebersteuern_distance, uebersteuern_max_angle])
                        self.lfs_connector.drift_values = uebersteuern_data
                        print(uebersteuern_data)

                if circular_difference(heading,
                                       direction) > 70 and self.lfs_connector.vehicle_model.speed > 5 and failed is None:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast dich gedreht."
                    self.os.UI.draw_info_button(reason)

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)

                if uebersteuern:
                    uebersteuern_max_angle = max(uebersteuern_max_angle, circular_difference(heading, direction))
                    avg_speed[0] += self.lfs_connector.vehicle_model.speed
                    avg_speed[1] += 1

                for i, tyre in enumerate(self.lfs_connector.vehicle_model.tire_data):
                    if i == 2 or i == 3:
                        steering = self.lfs_connector.vehicle_model.steering_input
                        if (tyre.get("slip_fraction") < -0.007 and self.lfs_connector.vehicle_model.speed > 10 and
                                (steering > 0.2 or steering < -0.2)):
                            if i == 2:
                                understeering_l = True
                            elif i == 3:
                                understeering_r = True
                        else:
                            if i == 2:
                                understeering_l = False
                            elif i == 3:
                                understeering_r = False
                if brake > 0.02:
                    understeering_r = False
                    understeering_l = False

                if self.lfs_connector.hit_an_object and failed is None:
                    print("pylone getroffen drift")
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)

                if understeering_r and understeering_l and not understeering:
                    understeering = True
                    understeering_timer = time.perf_counter()

                elif (not understeering_r and not understeering_l) and understeering:
                    understeering = False
                    understeering_time = time.perf_counter() - understeering_timer
                    if understeering_time > 0.22:
                        self.lfs_connector.hit_an_object = False
                        failed = time.perf_counter() if failed is None else failed
                        reason = "Du hast stark untersteuert."
                        self.os.UI.draw_info_button(reason)

                restart, quit = handle_button_clicks()
                if self.lfs_connector.laps_done == 1:
                    quit = True
                    break
                if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                    print("restarting")
                    restart = True
                    break

                if quit:
                    break
                time.sleep(0.1)

            if restart:
                cleanup_and_restart()
            elif quit:
                cleanup_and_quit()

        def handle_understeer():
            def circular_difference(a, b, max_value=65536):
                """
                Calculate the circular difference between two numbers in a range of 0 to max_value.

                Parameters:
                    a (int): The first number.
                    b (int): The second number.
                    max_value (int): The maximum value of the range (default is 65536).

                Returns:
                    int: The circular difference between a and b.
                """
                # Ensure both numbers are within the range
                a %= max_value
                b %= max_value

                # Calculate the circular difference
                diff = abs(a - b)
                return min(diff, max_value - diff) / 182.04

            """Handle understeer exercise"""
            understeering_l = False
            understeering_r = False
            understeering = False
            understeering_timer = time.perf_counter()
            understeering_count = 0
            failed = None
            FAILURE_DISPLAY_TIME = 2  # seconds

            while True:
                brake = self.lfs_connector.vehicle_model.brake
                heading = self.lfs_connector.vehicle_model.heading
                direction = self.lfs_connector.vehicle_model.direction
                if circular_difference(heading,
                                       direction) > 8 and self.lfs_connector.vehicle_model.speed > 7 and failed is None:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Dein Heck ist ausgebrochen."
                    self.os.UI.draw_info_button(reason)
                for i, tyre in enumerate(self.lfs_connector.vehicle_model.tire_data):
                    if i == 2 or i == 3:
                        steering = self.lfs_connector.vehicle_model.steering_input
                        if (tyre.get("slip_fraction") < -0.007 and self.lfs_connector.vehicle_model.speed > 10 and
                                (steering > 0.2 or steering < -0.2)):
                            if i == 2:
                                understeering_l = True
                            elif i == 3:
                                understeering_r = True
                        else:
                            if i == 2:
                                understeering_l = False
                            elif i == 3:
                                understeering_r = False
                if brake > 0.02:
                    understeering_r = False
                    understeering_l = False
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)
                if understeering_r and understeering_l and not understeering:
                    understeering = True
                    understeering_timer = time.perf_counter()
                    print("Understeering start")
                elif (not understeering_r and not understeering_l) and understeering:
                    understeering = False
                    understeering_time = time.perf_counter() - understeering_timer
                    if understeering_time > 0.95:
                        understeering_count += 1
                        print("Understeering for: ", understeering_time)

                restart, quit = handle_button_clicks()
                if understeering_count == 3:
                    quit = True
                    break
                if restart or quit or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                    break
                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit:
                cleanup_and_quit()

        def handle_oversteer():
            """Handle oversteer exercise"""

            def circular_difference(a, b, max_value=65536):
                """
                Calculate the circular difference between two numbers in a range of 0 to max_value.

                Parameters:
                    a (int): The first number.
                    b (int): The second number.
                    max_value (int): The maximum value of the range (default is 65536).

                Returns:
                    int: The circular difference between a and b.
                """
                # Ensure both numbers are within the range
                a %= max_value
                b %= max_value

                # Calculate the circular difference
                diff = abs(a - b)
                return min(diff, max_value - diff) / 182.04

            """Handle understeer exercise"""
            understeering_l = False
            understeering_r = False
            understeering = False
            understeering_timer = time.perf_counter()
            understeering_count = 0
            failed = None
            FAILURE_DISPLAY_TIME = 2  # seconds

            uebersteuern = False
            uebersteuern_timer = time.perf_counter()
            uebersteuern_count = 0
            uebersteuern_max_angle = 0
            uebersteuern_data = []
            avg_speed = [0, 0]
            while True:
                brake = self.lfs_connector.vehicle_model.brake
                heading = self.lfs_connector.vehicle_model.heading
                direction = self.lfs_connector.vehicle_model.direction
                if circular_difference(heading,
                                       direction) > 10 and self.lfs_connector.vehicle_model.speed > 15 and not uebersteuern:

                    uebersteuern = True
                    uebersteuern_timer = time.perf_counter()

                elif circular_difference(heading, direction) < 10 and uebersteuern:
                    print("Oversteering end")
                    uebersteuern = False
                    uebersteuern_time = time.perf_counter() - uebersteuern_timer
                    print(avg_speed)
                    uebersteuern_distance = uebersteuern_time * 0.277 * (avg_speed[0] / avg_speed[1])
                    print(uebersteuern_distance, uebersteuern_time)
                    avg_speed = [0, 0]
                    if 1 < uebersteuern_time < 5 < uebersteuern_distance:
                        uebersteuern_count += 1
                        print("Oversteering for: ", uebersteuern_time, "Distance: ", uebersteuern_distance)
                        uebersteuern_data.append([uebersteuern_time, uebersteuern_distance, uebersteuern_max_angle])
                        print(uebersteuern_data)
                    elif uebersteuern_time > 6:
                        failed = time.perf_counter() if failed is None else failed
                        reason = "Du bist zu lange ausgebrochen."
                        self.os.UI.draw_info_button(reason)
                if circular_difference(heading,
                                       direction) > 75 and self.lfs_connector.vehicle_model.speed > 5 and failed is None:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast dich gedreht."
                    self.os.UI.draw_info_button(reason)

                if uebersteuern:
                    uebersteuern_max_angle = max(uebersteuern_max_angle, circular_difference(heading, direction))
                    avg_speed[0] += self.lfs_connector.vehicle_model.speed
                    avg_speed[1] += 1

                for i, tyre in enumerate(self.lfs_connector.vehicle_model.tire_data):
                    if i == 2 or i == 3:
                        steering = self.lfs_connector.vehicle_model.steering_input
                        if (tyre.get("slip_fraction") < -0.007 and self.lfs_connector.vehicle_model.speed > 10 and
                                (steering > 0.2 or steering < -0.2)):
                            if i == 2:
                                understeering_l = True
                            elif i == 3:
                                understeering_r = True
                        else:
                            if i == 2:
                                understeering_l = False
                            elif i == 3:
                                understeering_r = False
                if brake > 0.02:
                    understeering_r = False
                    understeering_l = False

                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)

                if understeering_r and understeering_l and not understeering:
                    understeering = True
                    understeering_timer = time.perf_counter()

                elif (not understeering_r and not understeering_l) and understeering:
                    understeering = False
                    understeering_time = time.perf_counter() - understeering_timer
                    if understeering_time > 0.2:
                        self.lfs_connector.hit_an_object = False
                        failed = time.perf_counter() if failed is None else failed
                        reason = "Du hast stark untersteuert."
                        self.os.UI.draw_info_button(reason)

                restart, quit = handle_button_clicks()
                if uebersteuern_count == 3:
                    self.lfs_connector.store_laptime(f"{self.os.user_name, self.os.qnummer}",
                                                     self.lfs_connector.track.decode(), 0, uebersteuern_data)
                    quit = True
                    break
                if restart or quit or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                    break
                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit:
                cleanup_and_quit()

        def handle_freies_ueben():
            while True:
                restart, quit = handle_button_clicks()
                if restart or quit:
                    break
                time.sleep(0.1)

            if restart:
                cleanup_and_restart()
            elif quit:
                cleanup_and_quit()

        def handle_ideal_sicherheitslinie():
            connector = self.lfs_connector
            connector.laps_done = 0
            failed = None
            FAILURE_DISPLAY_TIME = 3

            while True:
                restart, quit = handle_button_clicks()
                if restart or quit:
                    print("restart or quit")
                    break

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du bist nicht Sicherheitslinie gefahren."
                    self.os.UI.draw_info_button(reason)


                if (connector.laps_done == 2 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    break
                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or connector.laps_done == 2:
                cleanup_and_quit()

        def handle_instructor_b2():
            """Handle practice exercises (PracticeBL1 and PracticeWE2)"""
            connector = self.lfs_connector
            connector.laps_done = 0
            failed = None
            FAILURE_DISPLAY_TIME = 3
            ai_strength = 5

            while True:
                restart, quit = handle_button_clicks()
                if restart or quit:
                    print("restart or quit")
                    break

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du bist nicht Idealline gefahren."
                    self.os.UI.draw_info_button(reason)
                if connector.laps_done + 2 != ai_strength:
                    setting = connector.laps_done + 2
                    if setting > 5:
                        setting = 5
                    command = f"/aiset_all {setting}"
                    command = command.encode()
                    self.send_commands_to_lfs([command])
                    ai_strength = setting

                if (connector.laps_done == 4 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    break
                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or connector.laps_done == 4:
                cleanup_and_quit()


        def handle_emergency_brake_b2():
            """Handle the emergency brake exercise (Notbremsung)"""
            MIN_SPEED = 110
            if uebung == "Doppelspurwechsel":
                MIN_SPEED = 88
            if uebung == "Notbremsung_220":
                MIN_SPEED = 216
            if uebung == "ABS_NoABS":
                MIN_SPEED = 155
            FAILURE_DISPLAY_TIME = 2  # seconds

            connector = self.lfs_connector

            checkpoint = 0
            failed = None

            def check_speed():
                if connector.vehicle_model.speed < MIN_SPEED:
                    return time.perf_counter(), "Du warst nicht schnell genug."
                return None, ""

            while True:
                restart, quit = handle_button_clicks()

                # Process checkpoints and speed checks
                if len(connector.splittimes) == 1 and checkpoint == 0:
                    checkpoint = 1
                    failed, reason = check_speed()
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)

                # Check for collisions
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)

                if connector.crossed_checkpoint2 and not connector.came_to_standstill:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast nicht angehalten."
                    self.os.UI.draw_info_button(reason)
                    connector.crossed_checkpoint1 = False
                    connector.crossed_checkpoint2 = False
                    connector.came_to_standstill = False

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)

                # Check exit conditions
                if (connector.laps_done == 1 or
                        (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    break
                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit or connector.laps_done == 1:
                cleanup_and_quit()

        def handle_abs_no_abs():
            """Handle the emergency brake exercise (Notbremsung)"""
            MIN_SPEED = 155

            FAILURE_DISPLAY_TIME = 2  # seconds

            connector = self.lfs_connector

            checkpoint = 0
            failed = None

            def check_speed():
                if connector.vehicle_model.speed < MIN_SPEED:
                    return time.perf_counter(), "Du warst nicht schnell genug."
                return None, ""

            self.os.UI.draw_info_button("Fahre 160 an der Linie.")
            info = time.perf_counter()
            while True:
                restart, quit = handle_button_clicks()
                if info != 0 and info < time.perf_counter() - 3:
                    self.os.UI.draw_info_button("Bremse dann in die Kurve.")
                if info != 0 and info < time.perf_counter() - 6:
                    info = 0
                    self.os.UI.del_info_button()
                # Process checkpoints and speed checks
                if len(connector.splittimes) == 1 and checkpoint == 0:
                    checkpoint = 1
                    failed, reason = check_speed()
                    if failed is not None:
                        self.os.UI.draw_info_button(reason)

                # Check for collisions
                if self.lfs_connector.hit_an_object and failed is None:
                    self.lfs_connector.hit_an_object = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Pylone getroffen."
                    self.os.UI.draw_info_button(reason)

                if connector.crossed_checkpoint2 and not connector.came_to_standstill:
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast nicht angehalten."
                    self.os.UI.draw_info_button(reason)
                    connector.crossed_checkpoint1 = False
                    connector.crossed_checkpoint2 = False
                    connector.came_to_standstill = False

                if self.lfs_connector.penalty and failed is None:
                    self.lfs_connector.penalty = False
                    failed = time.perf_counter() if failed is None else failed
                    reason = "Du hast eine Strafe erhalten."
                    self.os.UI.draw_info_button(reason)

                if connector.laps_done == 1 and self.abs_run:
                    print("Changing run")
                    self.abs_run = False
                    lfs_interface = self.os.lfs_interface
                    lfs_interface.send_commands_to_lfs([b"/spec"])
                    time.sleep(0.02)
                    lfs_interface.send_commands_to_lfs([b"/setup Road_NoAbs"])
                    time.sleep(0.02)
                    lfs_interface.send_commands_to_lfs([b"/join"])

                    break


                elif connector.laps_done == 1 and not self.abs_run:
                    print("Stop run")
                    quit = True
                    break

                print(connector.laps_done)
                # Check exit conditions
                if ((failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME) or
                        restart or quit):
                    print("rst run")
                    break

                time.sleep(0.1)

            if restart or (failed is not None and failed < time.perf_counter() - FAILURE_DISPLAY_TIME):
                cleanup_and_restart()
            elif quit:
                self.abs_run = True
                cleanup_and_quit()
            elif connector.laps_done == 1 and not self.abs_run:
                cleanup_and_restart()



        # Map exercise names to their handler functions
        exercise_handlers = {
            "Lenkradhaltung": handle_steering_wheel,
            "Notbremsung": handle_emergency_brake,
            "Notbremsung_Ausweichen": handle_emergency_brake,
            "Ausweichen": handle_evade,
            "untersteuern": handle_understeer,
            "uebersteuern": handle_oversteer,
            "HotlapBL1": handle_hotlap,
            "HotlapWE2": handle_hotlap,
            "PracticeBL1": handle_practice,
            "PracticeWE2": handle_practice,
            "Driften": handle_driften,
            "freies_ueben": handle_freies_ueben,
            "Zielbremsung": handle_zielbremsung,
            "Schnelles_Ausweichen": handle_emergency_brake,
            "Notbremsung_Kurve": handle_emergency_brake_b2,
            "Doppelspurwechsel": handle_emergency_brake_b2,
            "Halbkreis_drift": handle_oversteer,
            "Ideal_Sicherheitslinie": handle_ideal_sicherheitslinie,
            "Rennrunde_fahren": handle_instructor_b2,
            "Notbremsung_220": handle_emergency_brake_b2,
            "ABS_NoABS": handle_abs_no_abs
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
            if (command == b"/spec" or command == b"/shift x") and self.abs_run:
                self.lfs_connector.send_message(b"/spec AI 1")

    def update(self):
        pass

    def start_singleplayer(self):
        time.sleep(0.3)
        pyautogui.click(2644, 1267)
        time.sleep(0.5)
        pyautogui.click(3549, 671)
        time.sleep(0.5)
        pyautogui.click(1748, 1377)
        time.sleep(1)

    def start_singleplayer_after_track(self):
        time.sleep(0.3)
        pyautogui.click(2644, 1267)
        time.sleep(0.5)
        pyautogui.click(3549, 671)
        time.sleep(0.2)
