# .JSON DICTIONARY FOR TORNADOCOEFF.PY
# Written by Grayson Armour for tornadocoeff, September 2020
# -----------------------------------------------------------------
# The input to PyVLM is a .json file in the format below that describes both the wing's geometry and the current state.
# Geometry is described as five partitions (the five 'sections' under 'Wing'), each defined individually. The
# enterdata() function takes command-line inputs and inserts them into the proper locations in the .json structure.
# This data structure is then converted into an actual .json in tornadocoeff.

import constant as const

json_dict = {
    "name": "Morphing Wing",
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
            "numc": const.N_CHORD_PANELS,
            "cspace": "cosine",
            "sections": [
                {
                    #  x/y/z-le describe where the leading edge of each partition is relative to the (0,0,0) ref point
                    "xle": 0.0,
                    "yle": 0 * const.PARTITION_SPAN,
                    "zle": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "numb": 25,  # Number of span-wise panels for this partition; increase for higher fidelity model
                    "bspace": "semi-cosine",
                    "airfoil": const.AIRFOIL_BASE,
                },
                {
                    "xle": 0.0,
                    "yle": 1 * const.PARTITION_SPAN,
                    "zle": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "numb": 25,
                    "bspace": "semi-cosine",
                    "airfoil": const.AIRFOIL_BASE
                },
                {
                    "xle": 0.0,
                    "yle": 2 * const.PARTITION_SPAN,
                    "zle": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "numb": 25,
                    "bspace": "semi-cosine",
                    "airfoil": const.AIRFOIL_BASE  # MFC 1 (inner)
                },
                {
                    "xle": 0.0,
                    "yle": 3 * const.PARTITION_SPAN,
                    "zle": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "numb": 25,
                    "bspace": "semi-cosine",
                    "airfoil": const.AIRFOIL_BASE,
                },
                {
                    "xle": 0.0,
                    "yle": 4 * const.PARTITION_SPAN,
                    "zle": 0.0,
                    "chord": const.CHORD,
                    "angle": const.DIHEDRAL,
                    "numb": 25,
                    "bspace": "semi-cosine",
                    "airfoil": const.AIRFOIL_BASE, # MFC 2 (outer)
                }
            ],
        }
    ],
    "cases": [
        {
            "name": "Test",
            "alpha": const.DEFAULT_ALPHA,
            "speed": const.DEFAULT_AIRSPEED,
            "density": const.RHO
        }
    ]
}


def enterdata(airspeed, alpha, mfc1, mfc2):
    json_dict["surfaces"][0]["sections"][2]["airfoil"] = const.JSON_PATH + str(mfc1).replace("-", "n") + ".DAT"  # MFC 1
    json_dict["surfaces"][0]["sections"][4]["airfoil"] = const.JSON_PATH + str(mfc2).replace("-", "n") + ".DAT"  # MFC 2
    json_dict["cases"][0]["speed"] = float(airspeed)
    json_dict["cases"][0]["alpha"] = float(alpha)
    return json_dict


