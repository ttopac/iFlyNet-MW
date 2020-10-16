from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
XVAL = np.arange(0,8,4) #100
YVAL = np.arange(0,12,4) #304
xgrid, ygrid = np.meshgrid(XVAL, YVAL)
zgrid = np.zeros((xgrid.shape[0], xgrid.shape[1])) #76,25

myplot = ax.plot_surface(xgrid, ygrid, zgrid)
initvec = myplot._vec

def randinc(zgrid):
  '''
  Helper function to randomly increase (37,17) portion of the surface (about half)
  '''
  randarr = np.random.rand(37,17)
  zgrid[0:37, 0:17] += randarr
  return zgrid

# def plot_init():
#   myplot.set_verts(np.ones((xgrid.shape[0], xgrid.shape[1])).flatten(), '-z')
#   return myplot,

def plot_live(i, zgrid):
  newzgrid = randinc(zgrid)
  # myplot.set_verts((xgrid, ygrid, newzgrid.T.flatten()))
  myplot.set_verts(((initvec+i/100)[0:3].T))
  myplot.do_3d_projection(fig._cachedRenderer)
  print (myplot._vec[0][0])
  return myplot,


ani = FuncAnimation(fig, plot_live, fargs=(zgrid,), interval=0.5*1000, blit=True)

ax.set_xlabel('chord')
ax.set_ylabel('span')
ax.set_zlabel('deflection')
plt.show()
