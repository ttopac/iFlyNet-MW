# Only for estimation. Do not use for control (yet)!!!
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
stateCond = ''
liftHist = np.array([[0,0]])

#Initialize the plot
style.use ('fivethirtyeight')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)


#Initialize the GUI
root = tk.Tk()
root.title ("Airspeed and Angle of Attack prediction")
stateText = tk.Label(root, text=stateCond, height=10, width=30,font=('Arial', 26, 'bold'), justify='center')

def update_label():
  global stateCond
  a = str(time.time())
  stateText.config(text=stateCond)
  root.after(1000,update_label)

def predict1d(data, model, stateLabels):
  data_rsp = np.copy(data).reshape((1,2800,4))
  prediction = model.predict(data_rsp)
  predictedlabel = np.argmax (prediction)
  predictedstate = stateLabels[predictedlabel]
  return predictedstate

def acquireData(means, stddevs, stateclassifier, stateLabels):
  with nidaqmx.Task() as task:
    global stateHist
    global liftHist

    counter = 0
    # Define NiDAQmx tasks
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai2") #PZT_LB
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai3") #PZT_LT
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai1") #PZT_RB
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=350.0) #Commercial_SG_onWing
    task.timing.cfg_samp_clk_timing(rate=7000, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=7000)

    while True:
      lift = list()
      curtime = list()

      if counter == 0:
        startTime = time.time()
        data = np.asarray(task.read(number_of_samples_per_channel=2800))
        data[-1,:] *= 1000000 #Added in Nov as we have microstrain in Nov training.
        SGmean = np.mean(data[-1,:])
        data[-1,:] -= SGmean
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
        captured [-1,:] *= 1000000 #Added in Nov as we have microstrain in Nov training.
        captured [-1,:] -= SGmean
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

      # Estimate state probability and create probability list
      state_prob = predict1d(data.T, stateclassifier, stateLabels) #Expected input to the model is (2800,4)
      print (state_prob)
      
          
def controlAoA(arduinoData, threshold=0.5):
  global stateHist
  global stateCond
  
# def plotLive (i):
#   global liftHist
#   ax1.clear()
#   ax1.plot(liftHist[:,0], abs(liftHist[:,1]))
#   plt.xlim(0,90)
#   plt.ylim(-5,70)
#   plt.ylabel('Microstrain')
#   plt.title('Strain at root')

def main():
  global stateCond

  # Standardization coefficients (for Dec1_2019 training)
  means = [-0.0003843397694300264, 8.809781868417168e-05, -6.679369233817981e-05, -24.263946686701814] # As obtained from training data
  stddevs = [0.022034465589213872, 0.016842345002146333, 0.019794170241136142, 15.01779405490534] # As obtained from training data

  stateclassifier = load_model('g:/Shared drives/WindTunnelTests-Feb2019/Nov2019_Tests/Baseline_Tests/Kerasfiles/Dec1_models/Dec1_model2_state_val89_4sens.hdf5')
  stateLabels = pickle.load(open("g:/Shared drives/WindTunnelTests-Feb2019/Nov2019_Tests/Baseline_Tests/Kerasfiles/statelist.pickle",'rb'))
  #arduinoData=serial.Serial('com3',19200) #Initialize Arduino controller
  #stateclassifier._make_predict_function()
  acquireData(means, stddevs, stateclassifier, stateLabels)

  #executor = ThreadPoolExecutor(max_workers=1)
  #executor.submit(acquireData, means, stddevs, stateclassifier)
  #executor.submit(controlAoA, arduinoData, threshold=threshold)

  # Plot the data
  # canvas = FigureCanvasTkAgg(fig, master=root)
  # canvas.get_tk_widget().grid(column=0, row=1)
  # stateText.grid(column=0, row=2)
  # ani = animation.FuncAnimation(fig, plotLive, interval=1000)

  #update_label()
  #root.mainloop()


if __name__ == '__main__':
  main()
  
