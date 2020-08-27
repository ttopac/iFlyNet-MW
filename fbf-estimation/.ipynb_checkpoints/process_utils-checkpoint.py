#%% Import libraries and define functions 
import os
import numpy as np
import matplotlib.pyplot as plt
from keras.models import load_model

def predict1d(data, model, windowsize=1000, sensorcount=3):
    data_rsp = np.copy(data).reshape((1,windowsize,sensorcount))
    prediction = model.predict(data_rsp)
    return prediction[0][1] #Stall probability is given by 2nd element

def predict1d_state (data, model, windowsize=1000, sensorcount=3):
    data_rsp = np.copy(data).reshape((1,windowsize,sensorcount))
    prediction = model.predict(data_rsp)
    return prediction[0] #State estimation between 0-44

# The following function converts a single test data in .txt into a (N,1000,3) np array for model.predict
def convert_to_np_labview_single (txt_file, sensor='PZTLB', windowsize=1000): 
    maxwindows = len(open(txt_file).readlines(  ))//windowsize
    sensormap = {'PZTRB':7, 'PZTLB':8,'PZTLT':9, 'SG':11}
    examples = np.zeros((1,maxwindows*windowsize))
    examples[0,:] = np.loadtxt(txt_file,usecols=sensormap[sensor],max_rows=maxwindows*windowsize) #Columns: 7: PZTRB, 8: PZTLB, 9: PZTLT, 11: SG
    examples = np.reshape(examples.T,(-1,windowsize,1))
    return examples

# The following function converts a single test data in .txt into a (N,1000,3) np array for model.predict
def convert_to_np_dat (txt_file, max_rows=354000): 
    examples = np.zeros((1,354000))
    examples[0,:] = np.loadtxt(txt_file,usecols=0,max_rows=max_rows) #Columns: 7: PZTRB, 8: PZTLB, 9: PZTLT, 11: SG
    examples = np.reshape(examples.T,(-1,1000,1))
    return examples

# The following function converts a headerless labview output into a (N,1000,len(sensors)) np array for model.predict
# The order of sensors are PZTLB, PZTLT, PZTRB, SG.
# The latter sensors can be excluded (ex: we can have only PZTLB, PZTLT), but we cannot have latter sensors without former ones (ex: Only PZTRB not possible). This is consistent with CNN model.
def convert_to_np_labview_multi (txt_file, sensors, windowsize=1000):
    maxwindows = len(open(txt_file).readlines(  ))//windowsize
    sensormap = {'PZTRB':7, 'PZTLB':8,'PZTLT':9, 'SG':11}
    examples = np.zeros((len(sensors),maxwindows*windowsize))
    i = 0
    for sensor in sorted(sensors):
        tmp_example = np.loadtxt(txt_file, usecols = sensormap[sensor], max_rows=maxwindows*windowsize)
        examples[i,:] = tmp_example
        i += 1
    examples = np.reshape(examples.T,(-1,windowsize,len(sensors)))
    return examples

def export_np(rundir,testNpFile):
    testDat = np.load(rundir+testNpFile)
    np.savetxt('/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/FreqTest/txtFiles/{}_LB.txt'.format(testNpFile),testDat[0,:])
    np.savetxt('/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/FreqTest/txtFiles/{}_LT.txt'.format(testNpFile),testDat[1,:])
    np.savetxt('/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/FreqTest/txtFiles/{}_RB.txt'.format(testNpFile),testDat[2,:])

def plot_np(testNpFile):
    plt.plot(testNpFile)
    plt.show()

def show_ex_data(testNpFile):
    testDat = np.load(testNpFile)
    print(testDat[0,0:5])

def runModel (testFile, modelFile):
  classifier = load_model(modelFile)
  print (testFile.shape)
  newTestFile = testFile[:,:,0][:,:,np.newaxis]
  print (newTestFile.shape)
  pred = classifier.predict(newTestFile)
  return pred

def runModel2 (testFile, modelFile):
  classifier = load_model(modelFile)
  pred = classifier.predict(testFile)
  return pred