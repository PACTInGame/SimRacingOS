import time
import numpy as np
import pyinsim

class VehicleModel:
    def __init__(self, connector):
        self.speed_mci = None
        self.position_mci = None
        self.connector = connector
        # Existing attributes
        self.speed = 0.0
        self.previous_speed = 0.0
        self.dynamic = 0.0
        self.rpm = 0.0
        self.fuel = 0.0
        self.gear = 0
        self.angular_velocity = np.zeros(3)
        self.heading = 0.0
        self.direction = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.acceleration = np.zeros(3)
        self.velocity = np.zeros(3)
        self.position = np.zeros(3)
        self.throttle = 0.0
        self.brake = 0.0
        self.steering_input = 0.0
        self.tire_data = [
            {
                "x_force": 0.0,
                "y_force": 0.0,
                "vertical_load": 0.0,
                "air_temperature": 0.0,
                "slip_fraction": 0.0,
                "is_touching_ground": False,
            }
            for _ in range(4)
        ]
        self.road_friction_coefficient = 0.0
        self.road_slope_x = 0.0
        self.road_slope_y = 0.0

        # New attributes for outgauge data
        self.turbo = 0.0
        self.engine_temp = 0.0
        self.oil_pressure = 0.0
        self.oil_temp = 0.0
        self.clutch = 0.0
        self.tc_light = False
        self.abs_light = False
        self.handbrake_light = False
        self.battery_light = False
        self.oil_light = False
        self.eng_light = False

        # New attributes for outsim data
        self.engine_angular_velocity = 0.0
        self.max_torque_at_velocity = 0.0
        self.current_lap_distance = 0.0
        self.indexed_distance = 0.0
        self.steer_torque = 0.0

        # New attributes for data recording
        self.recording = False
        self.recorded_data = {
            'time': [],
            'angular_velocity': [],
            'slip_fraction': [],
            'steering': [],
            'speed': []
        }

        # args for friction:
        self.friction = 0
        self.rain_amount = 0
        self.temperature = 0
        self.measured_ang_vel = []
        self.set_speed = 10
        self.test_started_at = time.perf_counter()
        self.test_number = 0
        self.accelerator = 0
        self.steering = 0
        self.time_set_cursor = 0
        self.predictor = None
        self.turned_in = False
        self.turning_in_counter = 0
        self.difference_in_ang_vel = 0
        self.time_last_speed_update = time.perf_counter()
        self.distance_travelled = 0

    def update_outgauge(self, packet):
        self.previous_speed = self.speed
        # Calculate distance increment: speed * time
        self.speed = packet.Speed * 3.6  # Convert to km/h
        if self.speed < 1 and self.connector.crossed_checkpoint1 and not self.connector.came_to_standstill:
            self.connector.came_to_standstill = True
            self.connector.brake_distances.append([pyinsim.length(pyinsim.dist(self.position_mci,
                                                                               self.connector.brake_distance_start)),
                                                   self.connector.brake_speed_start])
            self.connector.brake_distance_start = 0
            self.connector.brake_speed_start = 0
            print("Brake distance: ", self.connector.brake_distances)

        self.dynamic = self.speed - self.previous_speed
        self.rpm = packet.RPM
        self.fuel = packet.Fuel
        self.gear = packet.Gear
        self.throttle = packet.Throttle
        self.brake = packet.Brake
        self.clutch = packet.Clutch
        self.turbo = packet.Turbo
        self.engine_temp = packet.EngTemp
        self.oil_pressure = packet.OilPress
        self.oil_temp = packet.OilTemp

        self.tc_light = pyinsim.DL_TC & packet.ShowLights > 0
        self.abs_light = pyinsim.DL_ABS & packet.ShowLights > 0
        self.handbrake_light = pyinsim.DL_HANDBRAKE & packet.ShowLights > 0
        self.battery_light = pyinsim.DL_BATTERY & packet.ShowLights > 0
        self.oil_light = pyinsim.DL_OILWARN & packet.ShowLights > 0
        self.eng_light = pyinsim.DL_ENGINE & packet.ShowLights > 0

    def update_outsim(self, packet):
        self.angular_velocity = np.array(packet.AngVel)
        #self.heading = packet.Heading taking MCI value instead
        self.pitch = packet.Pitch
        self.roll = packet.Roll
        self.acceleration = np.array(packet.Accel)
        self.velocity = np.array(packet.Vel)
        self.position = np.array(packet.Pos)
        self.steering_input = packet.Inputs[2]  # InputSteer
        self.gear = packet.Gear
        self.engine_angular_velocity, self.max_torque_at_velocity = packet.EngineData
        self.current_lap_distance, self.indexed_distance = packet.Distance
        self.steer_torque = packet.Extra[0]
        for i, wheel in enumerate(packet.Wheels):
            self.tire_data[i]["susp_deflect"] = wheel["SuspDeflect"]
            self.tire_data[i]["steer"] = wheel["Steer"]
            self.tire_data[i]["x_force"] = wheel["XForce"]
            self.tire_data[i]["y_force"] = wheel["YForce"]
            self.tire_data[i]["vertical_load"] = wheel["VerticalLoad"]
            self.tire_data[i]["ang_vel"] = wheel["AngVel"]
            self.tire_data[i]["air_temperature"] = wheel["AirTemp"]
            self.tire_data[i]["slip_fraction"] = wheel["SlipFraction"]
            self.tire_data[i]["is_touching_ground"] = wheel["Touching"] > 0

        self.friction = 1  # Default asphalt

    def estimate_road_slope(self):
        pass

    def update_car_data(self, car):
        self.position_mci = car.X, car.Y, car.Z
        self.speed_mci = car.Speed
        self.direction = car.Direction
        self.heading = car.Heading




