import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

# Contains the constants for tornadocoeff.py.

JSON_PATH = os.path.join(dir_path,"files/")
RESULTS_PATH = os.path.join(dir_path,"results/")


# Currently, there exist 13 different morph airfoils available, -6 through +6
MFC_MAX = 6
MFC_MIN = -6


# Overall wing definition data (partitions below follow and are repeated per partition). All distances in meters.
CHORD = .305
SPAN = .38
N_CHORD_PANELS = 20
N_SPAN_PANELS = 7
AIRFOIL_BASE = "NACA 0012"
MASS = 5


# Partition data
DIHEDRAL = 0
PARTITION_SPAN = .076


# State data
RHO = 1.19264  # Average air density in Palo Alto in September
DEFAULT_ALPHA = 6
DEFAULT_AIRSPEED = 12  # m/s
