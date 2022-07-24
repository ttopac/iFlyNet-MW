# .JSON DICTIONARY FOR TORNADOCOEFF.PY
# Written by Grayson Armour for tornadocoeff, September 2020
# -----------------------------------------------------------------
# The input to PyVLM is a .json file in the format below that describes both the wing's geometry and the current state.
# Geometry is described as five partitions (the five 'sections' under 'Wing'), each defined individually. The
# enterdata() function takes command-line inputs and inserts them into the proper locations in the .json structure.
# This data structure is then converted into an actual .json in tornadocoeff.

import os
import constant as const

json_dict = {
    "name": "Morphing Wing",
    "mach": 0,
    "sref": const.CHORD * const.SPAN,
    "cref": const.CHORD,
    "bref": const.SPAN,
    "xref": 0.0,  # (0,0,0) reference point refers to the wing's leading edge at root
    "yref": 0.0,
    "zref": 0.0,
    "surfaces": [
        {
            "name": "Wing",
            "angle": const.DIHEDRAL,
            "mirror": False,
            "cnum": const.N_CHORD_PANELS,
            "cspc": "cosine",
            "xpos": 0.0,
            "ypos": 0.029,
            "zpos": 0.0,
            "kirch_stall": False, #Below are stall parameters
            "a1": 19,
            "s1": 1.0,
            "s2": 2.7, #Decreasing makes stall deeper.
            "sections": [
                {
                    #  x/y/z-le describe where the leading edge of each partition is relative to the (0,0,0) ref point
                    "xpos": 0.0,
                    "ypos": 0 * const.PARTITION_SPAN,
                    "zpos": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "bnum": const.N_SPAN_PANELS,
                    "bspc": "equal",
                    "airfoil": const.AIRFOIL_BASE, # NACA0012
                },
                {
                    "xpos": 0.0,
                    "ypos": 1 * const.PARTITION_SPAN,
                    "zpos": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "bnum": const.N_SPAN_PANELS,
                    "bspc": "equal",
                    "airfoil": const.AIRFOIL_BASE, # NACA0012
                },
                {
                    "xpos": 0.0,
                    "ypos": 2 * const.PARTITION_SPAN,
                    "zpos": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "bnum": const.N_SPAN_PANELS,
                    "bspc": "equal",
                    "airfoil": const.AIRFOIL_BASE,  # MFC 1 (innerMFC, inner)
                },
                {
                    "xpos": 0.0,
                    "ypos": 3 * const.PARTITION_SPAN,
                    "zpos": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "bnum": const.N_SPAN_PANELS,
                    "bspc": "equal",
                    "airfoil": const.AIRFOIL_BASE, # MFC 1 (innerMFC, outer)
                },
                {
                    "xpos": 0.0,
                    "ypos": 4 * const.PARTITION_SPAN,
                    "zpos": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "bnum": const.N_SPAN_PANELS,
                    "bspc": "equal",
                    "airfoil": const.AIRFOIL_BASE, # MFC 2 (outerMFC, inner)
                },
                {
                    "xpos": 0.0,
                    "ypos": 5 * const.PARTITION_SPAN,
                    "zpos": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "bnum": 2,
                    "bspc": "equal",
                    "airfoil": const.AIRFOIL_BASE, # MFC 2 (outerMFC, outer)
                },
                {
                    "xpos": 0.0,
                    "ypos": (5 * const.PARTITION_SPAN)+0.015, #Extra rigid at the end section
                    "zpos": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "bnum": 2,
                    "bspc": "equal",
                    "airfoil": const.AIRFOIL_BASE, # NACA0012
                }
            ],
        },
        {
            "name": "Wall",
            "angle": 0.0,
            "mirror": False,
            "cnum": 45,
            "cspc": "equal",
            "xpos": 0.0,
            "ypos": 0.0,
            "zpos": 0.0,
            "sections": [
                {
                    "xpos": -0.305,
                    "ypos": 0.0,
                    "zpos": -0.2,
                    "chord": 0.915,
                    "angle": 0.0,
                    "bnum": 20,
                    "bspc": "equal",
                    "noload":True
                },
                {
                    "xpos": -0.305,
                    "ypos": 0.0,
                    "zpos": 0.2,
                    "chord": 0.915,
                    "angle": 0.0,
                    "noload":True
                }
            ]
      }
    ],
    "cases": [
        {
            "name": "Test",
            "alpha": 11.75,
            "speed": 12,
            "density": const.RHO,
        }
    ]
}


def enterdata(airspeed, alpha, mfc1, mfc2):
    json_dict["surfaces"][0]["sections"][2]["airfoil"] = os.path.join(const.AIRFOILS_PATH, str(mfc1) + ".DAT")  # MFC 1
    json_dict["surfaces"][0]["sections"][3]["airfoil"] = os.path.join(const.AIRFOILS_PATH, str(mfc1) + ".DAT")  # MFC 1
    json_dict["surfaces"][0]["sections"][4]["airfoil"] = os.path.join(const.AIRFOILS_PATH, str(mfc2) + ".DAT")  # MFC 2
    json_dict["surfaces"][0]["sections"][5]["airfoil"] = os.path.join(const.AIRFOILS_PATH, str(mfc2) + ".DAT")  # MFC 2
    json_dict["cases"][0]["speed"] = float(airspeed)
    json_dict["cases"][0]["alpha"] = float(alpha)+1.5 #correction for incorrect measurement.
    return json_dict


