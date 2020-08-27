import numpy as np
import matplotlib.pyplot as plt

npFile = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/RandomTest/sensorLocTest.npy')
plt.plot (npFile[0,:])
plt.plot (npFile[1,:])
plt.plot (npFile[2,:])
plt.legend (('LB','LT','RB'))
plt.show()