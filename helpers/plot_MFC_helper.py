import numpy as np
import matplotlib.pyplot as plt
import sys, os
from matplotlib import cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
sys.path.append(os.path.abspath('./helpers'))
from proc_tempcomp_helper import CommSG_Temp_Comp
from proc_MFCshape_helper import CalcMFCShape
import tkinter as tk
from multiprocessing import Process, Queue



class PlotMFCShape:
  def __init__(self, plot_refresh_rate, XVAL, YVAL):
    self.plot_refresh_rate = plot_refresh_rate
    self.fig = plt.figure(figsize=(3.0, 3.0))

    self.ax = self.fig.gca(projection='3d')
    self.xgrid, self.ygrid = np.meshgrid(XVAL, YVAL)

    self.ax.set_xlabel('chord (x) (mm)')
    self.ax.set_ylabel('span (y) (mm)')
    self.ax.set_zlabel('3D displacement (mm)')
    self.ax.set_zlim(-2, 2)
    # self.ax.auto_scale_xyz([0, 300], [0, 300], [-2, 2])

  def plot_twod_contour(self):
    self.mysurf = self.ax.plot_surface(self.xgrid, self.ygrid, np.zeros((self.xgrid.shape[0], self.xgrid.shape[1])), cmap=cm.coolwarm, linewidth=0)
    # self.fig.colorbar(self.mysurf, shrink=0.5, aspect=5)

    # Create fake bounding box for scaling
    minz, maxz = -3, 3 #mm
    max_range = np.array([self.xgrid.max() - self.xgrid.min(), self.ygrid.max() - self.ygrid.min(), maxz - minz]).max()
    Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (self.xgrid.max() + self.xgrid.min())
    Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (self.ygrid.max() + self.ygrid.min())
    Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (maxz + minz)
    # Uncomment following both lines to test the fake bounding box:
    for xb, yb, zb in zip(Xb, Yb, Zb):
      self.ax.plot([xb], [yb], [zb], 'w')

  def plot_live(self, i, queue):
    print ("Plotting live")
    while queue.qsize() > 1:
      read_shape = queue.get()
      # three_d_vertices = [list(zip(self.xgrid.reshape(-1), self.ygrid.reshape(-1), read_shape.reshape(-1)))]
      # self.mysurf.set_verts(three_d_vertices, closed=False)
      self.mysurf.remove()
      self.mysurf = self.ax.plot_surface(self.xgrid, self.ygrid, read_shape.T, cmap=cm.coolwarm, linewidth=0)
      return (self.mysurf,)


if __name__ == "__main__":
  #Test plotting in TK with fake data streaming in real-time.
  root = tk.Tk()
  root.title ("Real-time MFC Plotting")
  plot_refresh_rate = 1 #seconds

  mfc_shape = CalcMFCShape()
  q1 = Queue()
  p1 = Process(target = mfc_shape.supply_data, args=(q1, False, True))
  p1.start()

  plot = PlotMFCShape(plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL)
  plot.plot_twod_contour()

  canvas = FigureCanvasTkAgg(plot.fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=1)
  ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(q1,), interval=plot_refresh_rate*1000, blit=False)
  root.mainloop()