import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

# Contains the constants for tornadocoeff.py.

JSON_PATH = os.path.join(dir_path,"files")
RESULTS_PATH = os.path.join(dir_path,"results")
AIRFOILS_PATH = os.path.join(dir_path,"airfoils_2")

# Currently, there exist 13 different morph airfoils available, -6 through +6
MFC_MAX = 6
MFC_MIN = -6

# Overall wing definition data (partitions below follow and are repeated per partition). All distances in meters.
CHORD = .305
N_CHORD_PANELS = 20
N_SPAN_PANELS = 7
AIRFOIL_BASE = "NACA 4312"

# Partition data
DIHEDRAL = 0
PARTITION_SPAN = .076
SPAN = PARTITION_SPAN*5

# State data
RHO = 1.19264  # Average air density in Palo Alto in September
