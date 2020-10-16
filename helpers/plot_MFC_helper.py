from tests.scatter3d_demo2 import XVAL
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
import sys, os
from matplotlib import cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
sys.path.append(os.path.abspath('./helpers'))
import proc_MFCshape_helper
import tkinter as tk
from multiprocessing import Process, Queue



class PlotMFCShape:
  def __init__(self, plot_refresh_rate, XVAL, YVAL):
    self.plot_refresh_rate = plot_refresh_rate
    self.XVAL = XVAL
    self.YVAL = YVAL
    self.fig = plt.figure(figsize=(3.75, 3.75))
    plt.subplots_adjust(left=0, bottom=0, right=0.85, top=1.13, wspace=0, hspace=0)

    self.ax = self.fig.add_subplot(111, projection='3d')
    self.xgrid, self.ygrid = np.meshgrid(XVAL, YVAL)
    
    self.ax.set_xlabel('chord (x)', labelpad=-12, fontsize=11)
    self.ax.set_ylabel('span (y)', labelpad=-12, fontsize=11)
    self.ax.set_zlabel('3D displacement (mm)', labelpad=4, fontsize=11)
    self.ax.set_xticklabels([])
    self.ax.set_yticklabels([])
    self.ax.tick_params(labelsize="small")
    # self.ax.view_init(azim=0, elev=90)

    self.ax.set_zlim(-2, 2)
    # self.ax.auto_scale_xyz([0, 300], [0, 300], [-2, 2])

  def gen_vertices(self, Z):
    rows, cols = Z.shape
    stride=4 #This should be same as the downsampling number in proc_MFC_helper
    row_inds = list(range(0, rows-1, stride)) + [rows-1]
    col_inds = list(range(0, cols-1, stride)) + [cols-1]

    polys = []
    for rs, rs_next in zip(row_inds[:-1], row_inds[1:]):
      for cs, cs_next in zip(col_inds[:-1], col_inds[1:]):
        ps = [
          cbook._array_perimeter(a[rs:rs_next+1, cs:cs_next+1])
          for a in (self.xgrid, self.ygrid, Z)
        ]
        ps = np.array(ps).T
        polys.append(ps)
    return polys


  def plot_twod_contour(self):
    self.mysurf = self.ax.plot_surface(self.xgrid, self.ygrid, np.zeros((self.xgrid.shape[0], self.xgrid.shape[1])))
    self.initvec = self.mysurf._vec
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
    while queue.qsize() > 1: #This is here to keep up with the delay in plotting.
      try:
        _ = queue.get_nowait()
      except:
        pass
    try:
      read_shape = queue.get()
      new_verts = self.gen_vertices(read_shape)
      self.mysurf.set_verts(new_verts)
      self.mysurf.do_3d_projection(self.fig._cachedRenderer)
      # self.mysurf.remove()
      # self.mysurf, = self.ax.plot_surface(self.xgrid, self.ygrid, read_shape.T, cmap=cm.coolwarm, shade=True, vmin=-0.75, vmax=0.75, linewidth=0)
    except:
      pass  
    return (self.mysurf,)


if __name__ == "__main__":
  #Test plotting in TK with fake data streaming in real-time.
  root = tk.Tk()
  root.title ("MFC Plotting")
  plot_refresh_rate = 1 #seconds

  mfc_shape = proc_MFCshape_helper.CalcMFCShape()
  q1 = Queue()
  p1 = Process(target = mfc_shape.supply_data, args=(q1, False, True))
  p1.start()

  plot = PlotMFCShape(plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL)
  plot.plot_twod_contour()

  canvas = FigureCanvasTkAgg(plot.fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=1)
  ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(q1,), interval=plot_refresh_rate*1000, blit=False)
  root.mainloop()