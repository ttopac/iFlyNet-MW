# Written in MATLAB by Sara Ha. Adapted to Python by Tanay Topac.
# Only for shape estimation.
import os
from matplotlib.pyplot import plot
from nidaqmx.constants import AcquisitionType
import numpy as np
import sympy as sym
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as anim
import time

import sys, os
sys.path.append(os.path.abspath('./helpers'))
from daq_capturedata_helper import send_data

class CalcMFCShape():
  def __init__(self, plot_refresh_rate=1):
    self.plot_refresh_rate = plot_refresh_rate
    # Wing shape estimation constants
    self.ZTOP = 0.59531  # half of thickness (mm)
    DOWNSCALE_FACTOR = 4
    self.XVAL = np.arange(0,100,DOWNSCALE_FACTOR)  # (chord) continuous x from 0 to 100 mm
    self.YVAL = np.arange(0,304,DOWNSCALE_FACTOR)  # (span) continuous y from 0 to 304 mm
    self.X1LOC = np.asarray([15, 75]) #Middle 45 is missing because SG5 is not working.
    self.X2LOC = np.asarray([15, 75]) #Middle 45 is missing because SG8 is not working.
    self.YLOC = np.asarray([0, 126.6, 258.6])
  
  def estimate_shape_analytic(self, sensordata, queue):  # data.shape(6, num_datapoints), sgmean.shape(num_sensors), shape_hist=list
    # SGdata = sensordata #FOR FAKEDATA
    SGdata = np.mean(sensordata[9:14]/1E6, axis=1)
    
    # 1. Using polynomial fit, obtain strain distribution for each chord along strain1_fit=y=126.6 and strain2_fit=y=278.6 (x-axis)
    strain1_fit = np.polyfit(self.X1LOC, SGdata[0:3:2], 1)  # polynomial fit of order 2
    strain2_fit = np.polyfit(self.X2LOC, SGdata[3:5], 1)
    
    # 2. Obtain displacement for each chord along span of wing by integrating strain along chord (x-axis)
    x1 = sym.Symbol('x1')
    strain1_eq = strain1_fit[0] * x1 + strain1_fit[1] #TODO: Adapt this for 2 sensor case. This should be wrong currently.# Estimated equation for strain 1.
    d1_eq = sym.integrate(sym.integrate(strain1_eq, x1), x1)  # Estimated equation for displacement 1.
    f = sym.lambdify(x1, d1_eq)  # Convert the equation to numerical function that numpy can use.
    d1_val = f(self.XVAL)  # Calculate the displacement
    d1_val *= -self.ZTOP  # Calculate the displacement

    x2 = sym.Symbol('x2')
    strain2_eq = strain2_fit[0] * x2 + strain2_fit[1] #TODO: Adapt this for 2 sensor case. This should be wrong currently.
    d2_eq = sym.integrate(sym.integrate(strain2_eq, x2), x2)
    f = sym.lambdify(x2, d2_eq)
    d2_val = f(self.XVAL)
    d2_val *= -self.ZTOP

    # 3. Use polynomial fit to estimate displacement along the span (y-axis) 
    y_d = np.zeros((self.XVAL.shape[0], self.YVAL.shape[0]))
    for i in range(self.XVAL.shape[0]):
      y_d_fit = np.polyfit(self.YLOC, np.asarray([0, d1_val[i], d2_val[i]]), 2)  # polynomial fit of order 2
      y_d_i = np.polyval(y_d_fit, self.YVAL)
      y_d[i, :] = y_d_i
    queue.put_nowait(y_d)

  def read_from_xls(self,strains_file):
    strains_df = pd.read_excel(strains_file, sheet_name="cyclic_tanay", dtype=np.float32)
    strains_df = strains_df.loc[:, "ch1":]
    strains_np = strains_df.to_numpy()
    return strains_np

  def supply_data (self, shape_queue, data_queue=None, fakedata=False):
    if fakedata:
      excel_file_path = 'g:/My Drive/Research_Projects/2017_BRI_Project/May20_ShapeEstimation/exampleStrains.xlsx'
      # excel_file_path = '//Volumes/GoogleDrive/My Drive/Research_Projects/2017_BRI_Project/May20_ShapeEstimation/exampleStrains.xlsx'
      data = self.read_from_xls(excel_file_path)
      i = 0
      while i < data.shape[0]:
        self.estimate_shape_analytic(data[i,0:5], shape_queue)
        i += 1
        time.sleep(1)
    else:
      while True:
        while data_queue.qsize() > 1: #This is here to keep up with delay in plotting.
          try:  
            a = data_queue.get_nowait()
          except:
            pass
        try:
          sensordata = data_queue.get_nowait()
          data_queue.put_nowait(sensordata)
          self.estimate_shape_analytic(sensordata, shape_queue)
        except:
          pass
        time.sleep(self.plot_refresh_rate*4.5)
	