import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
import matplotlib.pyplot as plt
import time
import pickle
import numpy as np
from keras.models import load_model
import serial
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#Initialize the variables
stallCond = ''
stallList = list()
liftHist = np.array([[0,0]])

#Initialize the plot
style.use ('fivethirtyeight')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)


#Initialize the GUI
root = tk.Tk()
root.title ("Stall prediction")
stallText = tk.Label(root, text=stallCond, height=10, width=30,font=('Arial', 26, 'bold'), justify='center')

def update_label():
  global stallCond
  a = str(time.time())
  stallText.config(text=stallCond)
  root.after(1000,update_label)

def predict1d(data, model):
  data_rsp = np.copy(data).reshape((1,2800,data.shape[1]))
  prediction = model.predict(data_rsp)
  return prediction[0][1]

def acquireData3PZT(means, stddevs, stallclassifier):
  with nidaqmx.Task() as task:
    global stallList
    global liftHist

    counter = 0
    # Define NiDAQmx tasks
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai2") #PZT_LB
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai3") #PZT_LT
    #task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai1") #PZT_RB
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=350.0) #Commercial_SG_onWing
    task.timing.cfg_samp_clk_timing(rate=7000, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=7000)

    while True:
      lift = list()
      curtime = list()

      if counter == 0:
        startTime = time.time()
        data = np.asarray(task.read(number_of_samples_per_channel=2800))
        SGmean = np.mean(data[-1,:])
        for i in range(data.shape[0]-1):
          data[i,:] = (data[i,:]-means[i])/stddevs[i]
        # Append 28 points to liftHistory
        for i in range(28):
          lift.append((np.average(data[-1,i*100:(i+1)*100])-SGmean)*1000000)
          curtime.append(2800/7000/28*i)
        liftHist = np.append (liftHist,np.concatenate((np.expand_dims(np.asarray(curtime[0:2]), axis=1), np.expand_dims(np.asarray(lift[0:2]),axis=1)), axis=1), axis=0)

      else:
        elsetime = time.time() - startTime
        if elsetime > 90:
          elsetime = 0
          startTime = time.time()
          liftHist = np.array([[0,0]])
        captured = np.asarray(task.read(number_of_samples_per_channel=700))
        data [:,0:2100] = data [:,700:2800]
        data [:,-700:] = captured
        for i in range(data.shape[0]-1):
          data[i,-700:] = (data[i,-700:]-means[i])/stddevs[i]        
        # Append 7 points to liftHistory
        for i in range(7):
          lift.append((np.average(captured[-1,i*100:(i+1)*100])-SGmean)*1000000)
          curtime.append(elsetime + (700/7000/7*i))
        liftHist = np.append (liftHist,np.concatenate((np.expand_dims(np.asarray(curtime[0:2]), axis=1), np.expand_dims(np.asarray(lift[0:2]),axis=1)), axis=1), axis=0)
      counter += 1

      # Estimate stall probability and create probability list
      stall_prob = predict1d(data[:-1,:].T, stallclassifier)
      stallList.append(stall_prob)
      if len(stallList) > 5:
        del stallList[0]
          
def controlAoA(arduinoData, threshold=0.5):
  global stallList
  global stallCond
  
  while True:
    num_rot=1
    if sum(stallList) >= 3.0: # Stall
      dir='n'
      stallCond = "Stall"
      for a_iter in range(0,int(num_rot)):
        arduinoData.write(dir.encode())
        time.sleep(0.25)
    elif sum(stallList) <= 0.1: # No-stall
      dir='p'
      stallCond = "No Stall"
      for a_iter in range(0,int(num_rot)):
        arduinoData.write(dir.encode())
        time.sleep(0.25)
    else: #Indeterminate
      stallCond = "Inconclusive"
      time.sleep(0.25)
  
def plotLive (i):
  global liftHist
  ax1.clear()
  ax1.plot(liftHist[:,0], abs(liftHist[:,1]))
  plt.xlim(0,90)
  plt.ylim(-5,70)
  plt.ylabel('Microstrain')
  plt.title('Strain at root')

def main():
  global stallCond

  # Standardization coefficients (for Test2 training)
  means = [-0.0002862905522754296, 0.00014160949504295255]#, 2.983585730877926e-05] # As obtained from training data
  stddevs = [0.023828177361846174, 0.012151506564682033]#, 0.021041555452279762] # As obtained from training data

  stallclassifier = load_model('g:/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/KerasFiles/06222019_training/UnfilteredData/GOOD_06222019_StallOnly_99val_2800_2pzt.h5')
  threshold=0.5  # Threshold for stall classifiation: 0.5
  arduinoData=serial.Serial('com3',19200) #Initialize Arduino controller
  stallclassifier._make_predict_function()

  executor = ThreadPoolExecutor(max_workers=2)
  executor.submit(acquireData3PZT, means, stddevs, stallclassifier)
  executor.submit(controlAoA, arduinoData, threshold=threshold)

  # Plot the data
  canvas = FigureCanvasTkAgg(fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=1)
  stallText.grid(column=0, row=2)
  ani = animation.FuncAnimation(fig, plotLive, interval=1000)

  #stallText.pack()
  update_label()
  root.mainloop()


if __name__ == '__main__':
  main()
  
