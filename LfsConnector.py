import json
import os
import threading
import time
import pyinsim
from VehicleModel import VehicleModel


class LFSConnection:
    def __init__(self, username, qnummer, os):
        self.os = os
        self.username = username
        self.qnummer = qnummer
        self.penalty = False
        self.track = None
        self.text_entry = None
        self.in_game_cam = None
        self.insim = None
        self.outgauge = None
        self.outsim = None
        self.running = True
        self.vehicleID = 0
        self.obtain_PLID = True
        self.on_track = False
        self.vehicle_model = VehicleModel(self)
        self.game_time = 0
        self.is_connected = False
        self.current_lap_invalid = False
        self.next_hotlap_invalid = False
        self.splittimes = []
        self.buttons_clicked = []
        self.laps_done = 0
        self.uebung = ""
        self.hit_an_object = False
        self.crossed_checkpoint1 = False
        self.crossed_checkpoint2 = False
        self.crossed_checkpoint3 = False
        self.came_to_standstill = False
        self.brake_distances = []
        self.speeds = []
        self.brake_distance_start = 0
        self.brake_speed_start = 0
        self.drift_values = []


    def outgauge_packet(self, outgauge, packet):
        # TODO handle outgauge timeout
        self.game_time = packet.Time
        if self.obtain_PLID and self.on_track:
            self.vehicleID = packet.PLID
            self.obtain_PLID = False

        self.vehicle_model.update_outgauge(packet)

    def outsim_packet(self, outsim, packet):
        self.vehicle_model.update_outsim(packet)

    def button_click(self, insim, btc):
        print(self.buttons_clicked)
        self.buttons_clicked.append(btc.ClickID)

    def send_button(self, click_id, style, t, l, w, h, text, inst=0, typeIn=0):
        """
        This method checks if a button is already on the screen and if not, it sends a new button to LFS.
        It makes sending buttons easier than always sending the entire thing to lfs.
        """
        if type(text) == str:
            text = text.encode()
        self.insim.send(
            pyinsim.ISP_BTN,
            ReqI=255,
            ClickID=click_id,
            BStyle=style | 3,
            Inst=inst,
            T=t,
            L=l,
            W=w,
            H=h,
            Text=text,
            TypeIn=typeIn)

    def del_button(self, click_id):
        self.insim.send(pyinsim.ISP_BFN,
                        ReqI=255,
                        ClickID=click_id
                        )

    def get_car_data(self, insim, mci):
        for car in mci.Info:
            if car.PLID == self.vehicleID:
                self.vehicle_model.update_car_data(car)

    def send_message(self, message):
        print(message, "sent")
        self.insim.send(pyinsim.ISP_MST,
                        Msg=message)

    def stop(self):
        pyinsim.closeall()

    def get_pings(self, insim, ping):
        if not self.is_connected:
            self.is_connected = True
            print("connection to LFS successful")
            self.insim.send(pyinsim.ISP_TINY, ReqI=255, SubT=pyinsim.TINY_SST)

    def start_outgauge(self):
        try:
            self.outgauge = pyinsim.outgauge('127.0.0.1', 30000, self.outgauge_packet, 30.0)
        except:
            print("Failed to connect to OutGauge. Maybe it was still active.")

    def start_outsim(self):
        try:
            self.outsim = pyinsim.outsim('127.0.0.1', 29998, self.outsim_packet, 30.0)
        except:
            print("Failed to connect to OutSim. Maybe it was still active.")
        print("Outsim Started")

    def ping_insim(self):
        self.insim.send(pyinsim.ISP_TINY, ReqI=255, SubT=pyinsim.TINY_PING)

    def store_laptime(self, username, track_id, laptime, splittimes, filename='laptimes.json'):
        if self.uebung != "":
            track_id = track_id + self.uebung
            if track_id == "BL1HotlapBL1":
                track_id = "Hotlap Blackwood"
            elif track_id == "WE2HotlapWE2":
                track_id = "Hotlap Westhill"
            elif track_id == "BL1PracticeBL1":
                track_id = "Practice Blackwood"
            elif track_id == "WE2PracticeWE2":
                track_id = "Practice Westhill"
            elif track_id == "BL4Lenkradhaltung":
                track_id = "Lenkradhaltung"
            elif track_id == "BL4Notbremsung":
                track_id = "Notbremsung"
            elif track_id == "BL4Notbremsung_Ausweichen":
                track_id = "Notbremsung und Ausweichen"
            elif track_id == "BL4Ausweichen":
                track_id = "Ausweichen"
            elif track_id == "Bl4untersteuer":
                track_id = "Untersteuern"
            elif track_id == "BL4uebersteuern":
                track_id = "Übersteuern"
            elif track_id == "LA1Driften":
                track_id = "Driften"

            # TODO add other names
        # Check if the file exists
        if os.path.exists(filename):
            # Load the existing data
            with open(filename, 'r') as file:
                data = json.load(file)
        else:
            # Create an empty dictionary if the file does not exist
            data = {}
        # Check if the user exists in the data
        if username not in data:
            data[username] = {}

        # Check if the track exists for the user
        if track_id not in data[username]:
            data[username][track_id] = []

        # Append the new laptime and split times to the user's track data
        if self.uebung == "Notbremsung" or self.uebung == "Notbremsung_Ausweichen":
            speeds = [value[1] for value in self.brake_distances]
            distances = [value[0] for value in self.brake_distances]
            data[username][track_id].append({
                "laptime": laptime,
                "splittimes": splittimes,
                "brake_distances": distances,
                "speeds": speeds
            })
        elif self.uebung == "Ausweichen":
            data[username][track_id].append({
                "laptime": laptime,
                "splittimes": splittimes,
                "speeds": self.speeds
            })
        elif self.uebung == "uebersteuern":
            max_time = 0
            max_dist = 0
            max_ang = 0
            for split in splittimes:
                max_time = max(split[0], max_time)
                max_dist = max(split[1], max_dist)
                max_ang = max(split[2], max_ang)
            data[username][track_id].append({
                "laptime": max_time * 1000,
                "longest_distance": max_dist,
                "highest_angle": max_ang
            })
        elif self.uebung == "Driften":
            max_time = 0
            max_dist = 0
            max_ang = 0
            dist_total = 0
            for drift in self.drift_values:
                max_time = max(drift[0], max_time)
                max_dist = max(drift[1], max_dist)
                dist_total += drift[1]
                max_ang = max(drift[2], max_ang)

            data[username][track_id].append({
                "laptime": laptime,
                "splittimes": splittimes,
                "longest_time": max_time,
                "longest_distance": max_dist,
                "highest_angle": max_ang,
                "total_dist": dist_total
            })
        else:
            data[username][track_id].append({
                "laptime": laptime,
                "splittimes": splittimes
            })

        # Save the updated data back to the file
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

    def hot_lap_validity(self, insim, hlv):
        if len(self.splittimes) == 2:
            self.next_hotlap_invalid = True
        self.current_lap_invalid = True

    def get_split_times(self, insim, spx):
        print("Split-time")
        if len(self.splittimes) == 0 and spx.Split == 1:
            self.splittimes.append(spx.STime)
        elif len(self.splittimes) == 1 and spx.Split == 2:
            self.splittimes.append(spx.STime)
        elif len(self.splittimes) == 2 and spx.Split == 3:
            self.splittimes.append(spx.STime)
        else:
            if spx.Split == 1:
                self.splittimes = []
                self.splittimes.append(spx.Split)

    def get_laptimes(self, insim, lap):
        if lap.PLID == self.vehicleID:
            self.laps_done += 1
            print("Lap Finished")
            print("Split Times are ", self.splittimes)
            print("Current lap invalid", self.current_lap_invalid)
            print("Next Lap invalid", self.next_hotlap_invalid)
            if not self.current_lap_invalid:
                print(f"Store laptime for {self.vehicleID}, {self.track.decode}, {str(lap.LTime)}")
                self.store_laptime(f"{self.username, self.qnummer}", self.track.decode(), lap.LTime, self.splittimes)

            else:
                self.current_lap_invalid = False
            if self.next_hotlap_invalid:
                self.next_hotlap_invalid = False
                self.current_lap_invalid = True

    def get_checkpoint(self, number):
        # Use bitwise AND with 3 (binary 11) to get first two bits
        first_two_bits = number & 3

        # Compare first two bits
        checkpoints = {
            0b00: 3,
            0b01: 0,
            0b10: 1,
            0b11: 2
        }

        return checkpoints.get(first_two_bits, -1)

    def insim_state(self, insim, sta):
        """
        this method receives the is_sta packet from LFS. It contains information about the game state, that will
        be read and saved inside "flags" variable.
        """

        def start_game_insim():
            print("Game started")
            self.on_track = True
            insim.bind(pyinsim.ISP_MCI, self.get_car_data)
            insim.send(pyinsim.ISP_TINY, ReqI=255, SubT=pyinsim.TINY_NPL)
            self.start_outgauge()
            self.start_outsim()

        def start_menu_insim():
            print("Menu")
            self.os.lfs_interface.switched_to_menu = True
            self.time_menu_open = time.time()
            self.on_track = False
            insim.unbind(pyinsim.ISP_MCI, self.get_car_data)

        flags = [int(i) for i in str("{0:b}".format(sta.Flags))]
        self.in_game_cam = sta.InGameCam
        if len(flags) >= 15:
            game = flags[-1] == 1 and flags[-15] == 1

            if not self.on_track and game:
                start_game_insim()

            elif self.on_track and not game:
                start_menu_insim()

        elif self.on_track:
            start_menu_insim()

        self.text_entry = len(flags) >= 16 and flags[-16] == 1
        self.track = sta.Track

    def message_handling(self, insim, mso):
        try:
            message = mso.Msg.decode()
        except:
            pass

    def hit_object(self, insim, obh):
        self.hit_an_object = True

    def penalty_handling(self, insim, pen):
        print(pen.Reason)
        self.penalty = True

    def insim_checkpoints(self, insim, uco):
        if uco.UCOAction == pyinsim.UCO_CP_FWD:
            cp = self.get_checkpoint(uco.Info.Flags)
            if cp == 0:
                self.crossed_checkpoint1 = True
                self.brake_distance_start = self.vehicle_model.position_mci
                self.brake_speed_start = self.vehicle_model.speed
            elif cp == 1:
                self.crossed_checkpoint2 = True
            elif cp == 2:
                self.crossed_checkpoint1 = False
                self.crossed_checkpoint2 = False
                self.came_to_standstill = False

    def run(self):
        self.insim = pyinsim.insim(b'127.0.0.1', 29999, Admin=b'', Prefix=b"$",
                                   Flags=pyinsim.ISF_MCI | pyinsim.ISF_HLV | pyinsim.ISF_OBH | pyinsim.ISF_LOCAL,
                                   Interval=50)
        self.insim.bind(pyinsim.ISP_LAP, self.get_laptimes)
        self.insim.bind(pyinsim.ISP_SPX, self.get_split_times)
        self.insim.bind(pyinsim.ISP_STA, self.insim_state)
        self.insim.bind(pyinsim.ISP_MCI, self.get_car_data)
        self.insim.bind(pyinsim.TINY_PING, self.get_pings)
        self.insim.bind(pyinsim.ISP_MSO, self.message_handling)
        self.insim.bind(pyinsim.ISP_HLV, self.hot_lap_validity)
        self.insim.bind(pyinsim.ISP_BTC, self.button_click)
        self.insim.bind(pyinsim.ISP_OBH, self.hit_object)
        self.insim.bind(pyinsim.ISP_UCO, self.insim_checkpoints)
        self.insim.bind(pyinsim.ISP_PEN, self.penalty_handling)
        self.start_outgauge()
        self.start_outsim()
        pyinsim.run()


if __name__ == '__main__':
    LfsConnector = LFSConnection()
    thread = threading.Thread(target=LfsConnector.run)
    thread.start()
