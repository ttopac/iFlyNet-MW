import socket
import numpy as np
import threading
import time
import math
import sys, os

# for keyboard
from pynput.keyboard import Listener, Key, KeyCode
from collections import defaultdict
from enum import Enum
import subprocess 
import pickle

sys.path.append(os.path.abspath('./fbf-realtime'))

#from realtime_predictions_nogui_atharva import *

HEADER = 16
HEADER_SEND = 32
PORT = 5003

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8",80))
SERVER = s.getsockname()[0] 
s.close()
print(SERVER)

ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
# Lift = 1.0
# Drag = 2.0
# speed = 3.0

DEC_ACC = 10000

class Ctrl(Enum):
    (
        QUIT,
        CALIBRATE_FORCES,
        CALIBRATE_WINDSPEED,
        EXPERIMENT_START,
        TURN_LEFT,
        TURN_RIGHT
    ) = range(6)


QWERTY_CTRL_KEYS = {
    Ctrl.QUIT: Key.esc,
    Ctrl.CALIBRATE_FORCES: "f",
    Ctrl.CALIBRATE_WINDSPEED: "w",
    Ctrl.EXPERIMENT_START: "s",
    Ctrl.TURN_LEFT: Key.left,
    Ctrl.TURN_RIGHT: Key.right
}

AZERTY_CTRL_KEYS = QWERTY_CTRL_KEYS.copy()


## KEYBOARD CLASS
class KeyboardCtrl(Listener):
    def __init__(self, ctrl_keys=None):
        self._ctrl_keys = self._get_ctrl_keys(ctrl_keys)
        self._key_pressed = defaultdict(lambda: False)
        self._last_action_ts = defaultdict(lambda: 0.0)
        super(KeyboardCtrl,self).__init__(on_press=self._on_press, on_release=self._on_release)
        self.start()

    def _on_press(self, key):
        if isinstance(key, KeyCode):
            self._key_pressed[key.char] = True
        elif isinstance(key, Key):
            self._key_pressed[key] = True
        if self._key_pressed[self._ctrl_keys[Ctrl.QUIT]]:
            return False
        else:
            return True

    def _on_release(self, key):
        if isinstance(key, KeyCode):
            self._key_pressed[key.char] = False
        elif isinstance(key, Key):
            self._key_pressed[key] = False
        return True

    def quit(self):
        if self._key_pressed[self._ctrl_keys[Ctrl.QUIT]]:
            print("EXPERIMENT END")
            return not self.running or self._key_pressed[self._ctrl_keys[Ctrl.QUIT]]

    def cal_forces(self,forces):
        if self._key_pressed[self._ctrl_keys[Ctrl.CALIBRATE_FORCES]]:
            print("CALIBRATE FORCES")
            return forces
        else:
            return [0]

    def cal_speed(self,speed):
        if self._key_pressed[self._ctrl_keys[Ctrl.CALIBRATE_WINDSPEED]]:
            print("CALIBRATE SPEED")
            return speed
        else:
            return [0]

    def move_left(self):
        if self._key_pressed[self._ctrl_keys[Ctrl.TURN_LEFT]]:
            #print("CALIBRATE SPEED")
            return 1
        else:
            return 0
    
    def move_right(self):
        if self._key_pressed[self._ctrl_keys[Ctrl.TURN_RIGHT]]:
            #print("CALIBRATE SPEED")
            return 1
        else:
            return 0

    def start_experiment(self):
        if self._key_pressed[self._ctrl_keys[Ctrl.EXPERIMENT_START]]:
            #print("EXPERIMENT START")
            return 1
        else:
            return 0

    def _get_ctrl_keys(self, ctrl_keys):
        # Get the default ctrl keys based on the current keyboard layout:
        if ctrl_keys is None:
            ctrl_keys = QWERTY_CTRL_KEYS
            try:
                # Olympe currently only support Linux
                # and the following only works on *nix/X11...
                keyboard_variant = (
                    subprocess.check_output(
                        "setxkbmap -query | grep 'variant:'|"
                        "cut -d ':' -f2 | tr -d ' '",
                        shell=True,
                    )
                    .decode()
                    .strip()
                )
            except subprocess.CalledProcessError:
                pass
            else:
                if keyboard_variant == "azerty":
                    ctrl_keys = AZERTY_CTRL_KEYS
        return ctrl_keys

class ServerFunction(threading.Thread):
    def __init__(self):
        # Create the olympe.Drone object from its IP address
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.addr = None
        self.state1 = 0
        self.state2 = 0
        self.state3 = 0
        self.state_msg = "None"
        self.control = KeyboardCtrl()
        super().__init__()
        super().start()
    
    def start(self):
        self.server.bind(ADDR)
        self.server.listen()
        print(f"[LISTENING] Server is listening on {SERVER}")
        self.conn, self.addr = self.server.accept()
        print(f"[NEW CONNECTION] {self.addr} connected.")
        
    def state_message(self):
        if ((DEC_ACC*self.state1) and (not math.isnan(self.state1)) and (not math.isnan(self.state2)) and (not math.isnan(self.state3))):
            self.state_msg = ("#" + str(int(DEC_ACC*self.state1)) + "%" + str(int(DEC_ACC*self.state2)) + "%" + str(int(DEC_ACC*self.state3)) + "$")
        else:
            self.state_msg = "None"

    def update(self,raw_sensors):
        self.state1 = raw_sensors[14]
        self.state2 = raw_sensors[15]
        self.state3 = raw_sensors[6]

    def run(self): 
        while True:
            if (self.conn is not None):
                #self.state1 = self.raw1
                #self.state2 = self.raw2
                #self.state3 = self.raw3
                self.state_message()
                time.sleep(0.0005)
                send_msg = self.state_msg.encode(FORMAT)
                self.conn.send(send_msg)
                print("Raw sens2: ",send_msg)
                if self.control.quit():
                    time.sleep(1.0)
                    break
                    
        self.conn.close()
        self.server.close()