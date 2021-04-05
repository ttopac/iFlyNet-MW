import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
import pathlib
import os

filepath = pathlib.Path(__file__).parent.absolute()
assetpath = os.path.abspath(os.path.join(filepath, os.pardir, 'assets'))
sub_data = np.load(assetpath + "/sub_data.npy")

sample_rate = 7142
N = 2*sample_rate #2 seconds of data
time = np.linspace(0,2,N)

#First, plot the time-series data
# fig, ax = plt.subplots(figsize=(12, 6))
# ax.plot (time, sub_data)
# ax.set_xlabel ("Time (sec)")
# ax.set_ylabel ("Amplitude (V)")
# ax.set_title ("Time series data")
# plt.show()

#Second, get frequency domain data and plot.
freq = np.linspace (0.0, 512, int(N/2))
freq_data = fft(sub_data)
y = 2/N * np.abs(freq_data[0:np.int (N/2)])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(freq,y)
ax.set_xlabel ("Frequency (Hz)")
ax.set_ylabel ("Amplitude")
ax.set_title ("Frequency domain data")
plt.show()

