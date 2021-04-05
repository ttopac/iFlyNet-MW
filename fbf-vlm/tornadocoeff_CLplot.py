# CALCULATE COEFFICIENTS USING TORNADO VLM
# Written by Grayson Armour, September 2020
# -----------------------------------------------------------------
# This program is meant to calculate aero coefficients for a variable-geometry wing with two morphable sections in
# variable conditions. Given parameters describing environmental flight conditions (AoA, freestream velocity, etc.) and
# MFC morph states (from some negative bound to some positive bound), returns the coefficients of lift and drag. The
# PyVLM repository can be found here: https://github.com/Xero64/pyvlm


from pyvlm import latticesystem_from_json
from pyvlm.outputs.msh import latticeresult_to_msh
from IPython.display import display_markdown
from time import time
import json
import constant as const
import sys, os
from jsondict import enterdata
import pathlib
file_path = pathlib.Path(__file__).parent.absolute()
import matplotlib.pyplot as plt


# NAME FILE:
# ------------------------------
# Deterministically creates a string filename by concatenating the user inputs.
# Params: alpha, airspeed, mfc1, mfc2
# Returns: filename
def namefile(airspeed, alpha, mfc1, mfc2):
    unformatted = [airspeed, alpha, mfc1, mfc2]
    name = ""
    for i in range(len(unformatted)):
        currStr = str(unformatted[i])
        currStr = currStr.replace("-", "n")
        name += currStr
    name += ".json"
    return name


# MAKE JSON:
# ---------------------------------
# Coverts a given python dictionary and saves it as a json file.
# Params: python dictionary, name of file to be created
def makejson(dict, filename):
    with open(const.JSON_PATH + filename, 'w') as path:
        json.dump(dict, path)


# RETURN RESULTS
# ----------------------------------
# Process everything and return the results.
def return_results(airspeed, alpha, mfc1, mfc2):
    # 1) Create .json file using parameters and constants and name it deterministically
    filename = namefile(airspeed, alpha, mfc1, mfc2)
    json_dict = enterdata(airspeed, alpha, mfc1, mfc2)  # Enter data into the dictionary
    makejson(json_dict, filename)  # Convert dictionary into a .json file

    # 2) Generate lattice using PyVLM
    lsys = latticesystem_from_json(const.JSON_PATH + filename)

    return lsys



if __name__ == "__main__":
    airspeed = 12
    mfc1 = 0
    mfc2 = 0
    alphas = [0, 2, 4, 6, 8, 10, 12, 14, 16, 17, 18, 19, 20]
    # alphas = [0, 2]
    CL = list()

    for alpha in alphas:
        # Get results
        print ("Processing {} deg".format(alpha))
        lsys = return_results(airspeed, alpha, mfc1, mfc2)
        lres = lsys.results['Test']
        CL.append(lres.nfres.CL)

    plt.plot(alphas, CL)
    plt.show()