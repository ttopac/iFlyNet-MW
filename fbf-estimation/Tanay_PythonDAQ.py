import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
import matplotlib.pyplot as plt
import time
import pickle
import numpy as np
from keras.models import load_model
import serial
import time

with open ('g:/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/KerasFiles/06222019_training/stateDict.pickle', 'rb') as handle:
    stateDict = pickle.load(handle)

def predict1d(data, model):
    data_rsp = np.copy(data).reshape((1,2800,data.shape[1]))
    prediction = model.predict(data_rsp)
    return prediction[0][1]

def predict1d_state (data, model):
    data_rsp = np.copy(data).reshape((1,2800,data.shape[1]))
    prediction = model.predict(data_rsp)
    return prediction[0] #State estimation between 0-44

# Standardization coefficients (for Test2 training)
means = [-0.0002862905522754296, 0.00014160949504295255, 2.983585730877926e-05]#, -36.33824690045131] # As obtained from training data
stddevs = [0.023828177361846174, 0.012151506564682033, 0.021041555452279762]#, 15.658515723288968] # As obtained from training data

# Standardization coefficients (for Test3 training)
# means = [-0.0002973277247193029, 8.252501747471514e-05, -7.819776684918195e-06, -41.364817636075415]
# stddevs = [0.02804103550191247, 0.017217207585874576, 0.02953128117059045, 14.863605041549945]

SGmean = 0

stallclassifier = load_model('g:/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/KerasFiles/06222019_training/UnfilteredData/GOOD_06222019_StallOnly_96val_2800_3pzt_std.h5')
#stateclassifier = load_model('g:/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/KerasFiles/06272019_training/UnfilteredData/06272019_StateOnly_100val_2800_3pzt+SG_std.h5') #Test3
#stateclassifier = load_model('g:/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/KerasFiles/06222019_training/UnfilteredData/06222019_StateOnly_91val_2800_3pzt+SG_std.h5') #Test2
thr=0.5;  # Threshold stall classifiation: 0.5
p_hat=0;    # Set initial probability of stall as 0 (No-stall)
arduinoData=serial.Serial('com3',19200)

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai2") #PZT_LB
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai3") #PZT_LT
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai1") #PZT_RB
    #task.ai_channels.add_ai_voltage_chan("cDAQ1Mod5/ai0") #SensorNet_SG
    #task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=350.0) #Commercial_SG

    task.timing.cfg_samp_clk_timing(rate=7000, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=7000)
    #task.timing.samp_clk_rate = 10000 #SG Module Supports max. 10000 clock rate
    testdata = np.zeros((4,1))
    counter = 0
    stallpred = list()
    data = np.asarray([[0,0],[0,0]])
    while True:
        #Sera's part
        err=p_hat-thr

        # P-Controller
        if err>0.5-thr: #Stall
            K=20    # K: Proportional gain (Maximum step to rotate at maximum angle)
            u=10
            #u=K*err
        elif err<0.5-thr: #Non-stall
            K=20
            u=-10
            #u=K*err # K: Proportional gain (Maximum step to rotate at maximum angle)
        else:
            u=0 

        # Arduino Control 
        if stallpred.count(1) >= 3: # Stall
            #print("Wing is in stall")
            dir='n'
            num_rot=3
            for a_iter in range(0,int(num_rot)):
                arduinoData.write(dir.encode())
                time.sleep(0.01)
        elif stallpred.count(0) >= 3: # Not Stall
            #print("Wing is not in stall")
            dir='p'
            num_rot=3
            #num_rot=round(abs(u))
            for a_iter in range(0,int(num_rot)):
                arduinoData.write(dir.encode())
                time.sleep(0.01)


        #Tanay's part
        if counter == 0:
            data = np.asarray(task.read(number_of_samples_per_channel=2800))
            if data.shape[0] > 3: #Use first SG data for calibration (ONLY USE FOR REAL TIME ESTIMATION !!! FOR ACQUISITION COMMENT THIS CHANGE SGmean ABOVE
                SGmean = np.mean(data[3,:])
            counter += 1
        else:
            data = np.asarray(task.read(number_of_samples_per_channel=2800))
        
        if data.shape[0] <= 3:
            for i in range(data.shape[0]):
                data[i,:] = (data[i,:]-means[i])/stddevs[i]
        elif data.shape[0] > 3:
            for i in range(data.shape[0]-1):
                data[i,:] = (data[i,:]-means[i])/stddevs[i]
            data[3,:] = (data[3,:] - SGmean) * 1000000
        
        stall_prob = predict1d(data[0:3,:].T, stallclassifier)
        # state_probs = predict1d_state(data.T, stateclassifier)
        # state_est = stateDict[np.argmax(state_probs)]

        # testdata = np.concatenate((testdata,data),axis=1)
        if stall_prob > 0.5:
            stallpred.append(1)
        else:
            stallpred.append(0)
        if len(stallpred) > 5:
           del stallpred[0]
        
        #print (stall_prob)
        print (stallpred)
        #print (state_est)
        # if testdata.shape[1] > 200000:
        #     np.save('g:/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/StateTest/7000_20ms_20deg_noSTD.npy',testdata)
        #     break
        p_hat = stall_prob