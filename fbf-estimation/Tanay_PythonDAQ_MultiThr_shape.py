# Written in MATLAB by Sara Ha. Adapted to Python by Tanay Topac.
# Only for shape estimation. Do not use for control (yet)!
import os
import time
import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np
import sympy as sym
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from drawnow import drawnow
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as anim


# Wing shape estimation constants
ZTOP = 0.59531  # half of thickness (mm)
XVAL = np.arange(100)  # (chord) continuous x from 0 to 100 mm
YVAL = np.arange(304)  # (span) continuous y from 0 to 304 mm
XLOC = np.asarray([15, 45, 75])
YLOC = np.asarray([0, 126.6, 278.6])

def add_channels_to_NI():
	with nidaqmx.Task() as task:
		task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/aix1")  # SG_mfc_1
		task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/aix2")  # SG_mfc_2
		task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/aix3")  # SG_mfc_3
		task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/aix4")  # SG_mfc_4
		task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/aix5")  # SG_mfc_5
		task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/aix6")  # SG_mfc_6
		task.timing.cfg_samp_clk_timing(rate=7000, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=7000)
		return task


def read_from_xls(strains_file):
	strains_df = pd.read_excel("/"+strains_file, sheet_name="cyclic_tanay", dtype=np.float32)
	strains_df = strains_df.loc[:, "ch1":]
	strains_np = strains_df.to_numpy()
	return strains_np


def read_strains_manually():
	# Here we
	strains = np.asarray([0.00020759, 0.00040759, 0.00060759, 0.00030759, 0.00050759, 0.00070759])
	return strains


def read_from_NI(task, numsamples=700):
	data = np.asarray(task.read(number_of_samples_per_channel=numsamples))
	data = np.mean(data, axis=0)
	return data #This returns a 1D array


def SG_calibrate(data):
	sgmean = np.zeros(data.shape[0])
	for i in range(data.shape[0]):
		sgmean = np.mean(data[i, :], axis=1)
	return sgmean


def estimate_shape(captured, sgmean, shape_hist):  # data.shape(num_sensors, num_datapoints), sgmean.shape(num_sensors), shape_hist=list
	"""
	1. Input strain measurements
	"""
	captured -= sgmean

	"""
	2. Using polynomial fit, obtain strain distribution for each chord along
	strain1_fit=y=126.6 and strain2_fit=y=278.6 (x-axis)
	"""
	strain1_fit = np.polyfit(XLOC, captured[0:3], 2)  # polynomial fit of order 2
	strain1_est = np.polyval(strain1_fit, XVAL)  # strain1_est is estimated strain values using polynomial fit
	strain2_fit = np.polyfit(XLOC, captured[3:], 2)
	strain2_est = np.polyval(strain2_fit, XVAL)

	"""
	3. Obtain displacement for each chord along span of wing by integrating
	strain along chord (x-axis)
	"""
	x1 = sym.Symbol('x1')
	strain1_eq = strain1_fit[0] * x1 ** 2 + strain1_fit[1] * x1 + strain1_fit[2]  # Estimated equation for strain 1.
	d1_eq = sym.integrate(sym.integrate(strain1_eq, x1), x1)  # Estimated equation for displacement 1.
	f = sym.lambdify(x1, d1_eq)  # Convert the equation to numerical function that numpy can use.
	d1_val = f(XVAL)  # Calculate the displacement
	d1_val *= -ZTOP  # Calculate the displacement

	x2 = sym.Symbol('x2')
	strain2_eq = strain2_fit[0] * x2 ** 2 + strain2_fit[1] * x2 + strain2_fit[2]
	d2_eq = sym.integrate(sym.integrate(strain2_eq, x2), x2)
	f = sym.lambdify(x2, d2_eq)
	d2_val = f(XVAL)
	d2_val *= -ZTOP

	"""
	4. Use polynomial fit to estimate displacement along the span (y-axis) 
	"""
	y_d = np.zeros((XVAL.shape[0], YVAL.shape[0]))
	for i in range(XVAL.shape[0]):
		y_d_fit = np.polyfit(YLOC, np.asarray([0, d1_val[i], d2_val[i]]), 2)  # polynomial fit of order 2
		y_d_i = np.polyval(y_d_fit, YVAL)
		y_d[i, :] = y_d_i

	shape_hist.append(y_d)
	return shape_hist

def setup_plot():
	fig = plt.figure()
	ax = fig.gca(projection='3d')
	x, y = np.meshgrid(XVAL, YVAL)

	ax.set_xlabel('chord (x)')
	ax.set_ylabel('span (y)')
	ax.set_zlabel('3D displacement')
	ax.set_zlim(-1.5, 1.5)
	ax.auto_scale_xyz([0, 300], [0, 300], [-1.5, 1.5])
	return fig, ax, x, y

def plot_shape(ax, x, y, last_strain):
	mysurf = ax.plot_surface(x, y, last_strain.T, cmap=cm.coolwarm, linewidth=0, antialiased=True)
	fig.colorbar(mysurf, shrink=0.5, aspect=5)

	# Create fake bounding box for scaling
	max_range = np.array([x.max() - x.min(), y.max() - y.min(), last_strain.T.max() - last_strain.T.min()]).max()
	Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (x.max() + x.min())
	Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (y.max() + y.min())
	Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (last_strain.T.max() + last_strain.T.min())
	# Comment or uncomment following both lines to test the fake bounding box:
	for xb, yb, zb in zip(Xb, Yb, Zb):
		ax.plot([xb], [yb], [zb], 'w')

	plt.show()

def update_plot(frame_number, shape_hist, plot):
	plot[0].remove()
	plot[0] = ax.plot_surface(x, y, shape_hist[frame_number].T, cmap=cm.coolwarm, linewidth=0, antialiased=True)

if __name__ == '__main__':
	
	shape_hist = list()
	"""
	Run below for realtime
	"""
	# task = add_channels_to_NI()
	# data = read_from_NI(task, 2800)
	# sgmean = SG_calibrate(data)
	# while True:
	# 	data = read_from_NI(task)
	# 	shape_hist = estimate_shape(data, sgmean, shape_hist)
	""" Realtime end """

	"""
	Run below for testing the function
	"""
	# data = read_strains_manually()
	# shape_hist = estimate_shape(data, 0, shape_hist)
	# fig, ax, x, y = setup_plot()
	# plot_shape(ax, x, y, shape_hist[0])
	""" Testing end """

	"""
	Run below for testing continuous plotting of cyclic strain
	"""
	dataloc = os.path.join("Volumes", "GoogleDrive", "My Drive", "Research_Projects", "2017_BRI_Project",
	                       "May20_ShapeEstimation", "exampleStrains.xlsx")
	data = read_from_xls(dataloc)
	fig, ax, x, y = setup_plot()
	start = time.time()
	while data.shape[0] > 0:
		shape_hist = estimate_shape(data[0], 0, shape_hist)
		data = np.delete(data, 0, 0)

	mysurf = [ax.plot_surface(x, y, np.zeros((YVAL.shape[0], XVAL.shape[0])), cmap=cm.coolwarm, linewidth=0, antialiased=True)]
	fig.colorbar(mysurf[0], shrink=0.5, aspect=5)
	animate = anim.FuncAnimation(fig, update_plot, len(shape_hist), fargs=(shape_hist, mysurf), interval=100)

	# Create fake bounding box for scaling
	max_range = np.array([x.max() - x.min(), y.max() - y.min(), shape_hist[0].T.max() - shape_hist[0].T.min()]).max()
	Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (x.max() + x.min())
	Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (y.max() + y.min())
	Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (shape_hist[0].T.max() + shape_hist[0].T.min())
	# Comment or uncomment following both lines to test the fake bounding box:
	for xb, yb, zb in zip(Xb, Yb, Zb):
		ax.plot([xb], [yb], [zb], 'w')

	end = time.time()
	print (end-start)
	plt.show()
	""" Testing end """
