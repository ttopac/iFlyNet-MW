import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import sys, os
sys.path.append(os.path.abspath('./helpers'))
import proc_keras_estimates_helper

class PlotData:
  def __init__(self, xs, pred_freq, stall_model_path, liftdrag_model_path):
    self.xs = xs
    self.pred_freq = pred_freq
    self.stall_model_path = stall_model_path
    self.liftdrag_model_path = liftdrag_model_path
    
    self.fig = plt.figure()
    self.ax1 = self.fig.add_subplot(2,1,1) #Lift
    self.ax2 = self.fig.add_subplot(2,1,2) #Drag
    
    self.estimates = proc_keras_estimates_helper.iFlyNetEstimates(pred_freq, stall_model_path, liftdrag_model_path)
    self.init_common_params()

  def init_common_params (self):
    plt.style.use ('fivethirtyeight')
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
    mpl.rcParams['axes.edgecolor'] = 'black'
    mpl.rcParams['axes.linewidth'] = 1

    self.ax1.set_title("Lift", fontsize=11)
    self.ax1.set_xlabel("Time (sec)", labelpad=2, fontsize=11)
    self.ax1.set_ylabel("Microstrain (ue)", labelpad=2, fontsize=11)
    self.ax1.tick_params(labelsize="small")
    self.ax1.grid(False)
    self.ax2.set_title("Drag", fontsize=11)
    self.ax2.set_xlabel("Time (sec)", labelpad=2, fontsize=11)
    self.ax2.set_ylabel("Microstrain (ue)", labelpad=2, fontsize=11)
    self.ax2.tick_params(labelsize="small")
    self.ax2.grid(False)

  def term_common_params(self, realtime):
    # self.leg1 = self.ax1.legend(fontsize=7, loc="upper right", ncol=1, columnspacing=1)
    # Add legend for drag plot
    self.leg2 = self.ax2.legend(fontsize=7, loc="upper right", ncol=1, columnspacing=1)
    
    # Legend for lift is a little more complicated
    lns = self.ln1+self.ln2+self.ln3
    labs = [l.get_label() for l in lns]
    self.leg1 = self.ax1.legend(lns, labs, fontsize=7, loc="upper right", ncol=1, columnspacing=1)

    for line in self.leg1.get_lines():
      line.set_linewidth(1.5)
      line.set_markersize(1.5)
    for line in self.leg2.get_lines():
      line.set_linewidth(1.5)
    
    if realtime:
      pass
    else:
      self.fig.set_size_inches(6.0, 6.0)
      plt.tight_layout(pad=1.3)
    plt.show()

  def plot_liftdrag_real (self, ys, ref_temp=None):
    self.ln1 = self.ax1.plot(self.xs, -ys[14], linewidth=1.0, label="SG Lift")
    self.ax2.plot(self.xs, -ys[15], color='#ff7f0e', linewidth=1.0, label="SG Drag")

  def plot_stall_est (self, ys):
    preds = self.estimates.estimate_stall(ys, False)
    ax1_stalltwin = self.ax1.twinx()
    ax1_stalltwin.spines["right"].set_position(("axes", 1.02))
    ax1_stalltwin.spines["right"].set_edgecolor('r')
    self.ln3 = ax1_stalltwin.plot (self.xs, preds, "*", markersize=3, color='r', label="Stall?")
    ax1_stalltwin.set_ylabel("Stall?", fontsize=11)
    ax1_stalltwin.yaxis.label.set_color('r')
    loc = plticker.MultipleLocator(base=1.0) #Define ticker to put ticks only at 0 and 1
    ax1_stalltwin.yaxis.set_major_locator(loc)
    ax1_stalltwin.tick_params(colors = 'r', labelsize="x-small")
    ax1_stalltwin.grid(False)

  def plot_liftdrag_est (self, ys):
    preds = self.estimates.estimate_liftdrag(ys, False)
    self.ln2 = self.ax1.plot(self.xs, -preds[:,0], ':', color=self.ax1.lines[0].get_color(), linewidth=1.0, label="Predicted Lift")
    self.ax2.plot(self.xs, -preds[:,1], ':', color=self.ax2.lines[0].get_color(), linewidth=1.0, label="Predicted Drag")