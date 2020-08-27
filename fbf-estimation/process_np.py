#%% The following block can be used to convert numpy file into .txt file for processing in Matlab
import os
rundir = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/FreqTest/'
files = [f for f in os.listdir(rundir) if os.path.isfile(rundir+f) and f[-4:] == '.npy']

for file in files:
    export_np(rundir,file)

#%% The following block can be used for running predict on the data we collected using Tanay_PythonDAQ.py
# testNpFile = 'g:/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/test1.npy' #FOR WINDOWS
testNpFile = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/test1.npy' #FOR MAC
modelFile = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/KerasFiles/06072019_StallOnly_94val_2800w.h5'
testNp = np.load(testNpFile)

# Test with 1k sampling rate
#testNp_res = np.transpose(testNp[:,1:])
#testNp_res = np.reshape(testNp_res, (200,1000,3))

# Test with 2.8k sampling rate
#testNp_res = np.transpose(testNp[:,1:28001])
#testNp_res = np.reshape(testNp_res, (10,2800,3))

#plt.plot(testNp_res[0,:,0])
#plt.show()

pred = runModel(testNp_res,modelFile)
print (pred)

#%% The following block can be used for running predict on some training data
# Use window size = 1000
os.environ['KMP_DUPLICATE_LIB_OK']='True'
PZTLB_data = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/Test Data/Neural Network/X1.dat/PZTLB_20ms_16deg.dat' 
PZTLT_data = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/Test Data/Neural Network/X1.dat/PZTLT_20ms_16deg.dat' 
PZTRB_data = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/Test Data/Neural Network/X1.dat/PZTRB_20ms_16deg.dat' 
modelFile = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/KerasFiles/06072019_StallOnly_95val.h5'
some_train_ex = convert_to_np(PZTLB_data,PZTLT_data,PZTRB_data)

pred = runModel2(some_train_ex[200:220,:,:],modelFile)
print (pred)

#%% The following block can be used to plot the data from the old training set, and new dataset 
# Use window size = 1000
past_PZTLB_data = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/Test Data/Neural Network/X1.dat/PZTLB_20ms_2deg.dat' 
past_PZTLT_data = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/Test Data/Neural Network/X1.dat/PZTLT_20ms_2deg.dat' 
past_PZTRB_data = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/Test Data/Neural Network/X1.dat/PZTRB_20ms_2deg.dat' 
new_data = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 3/Labview/Airspeed20/Airspeed20_AOA2.txt'

old_ex = convert_to_np(past_PZTLB_data,past_PZTLT_data,past_PZTRB_data)
new_ex = convert_to_np_labview(new_data)

fig = plt.figure()
plt.subplot()

#%% The following block can be used for running predict on some test data taken from labview
# Use window size = 1000
os.environ['KMP_DUPLICATE_LIB_OK']='True'
modelFile = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/KerasFiles/06072019_StallOnly_95val.h5'
data = '/Volumes/Google Drive File Stream/Shared drives/Wind Tunnel Tests - Feb2019/Wind Tunnel Data 2/Test Data/Raw Data/032818ms/txt/Airspeed18_AOA10.txt'

some_test_ex = convert_to_np_labview(data)

pred = runModel2(some_test_ex[0:30,:,:],modelFile)
print (pred)

plt.plot(some_test_ex[0,:,1])
plt.show()

#%% The following block can be used to plot some data from a np array 
# Use window size = 1000
Jun19_npy = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/June2019_Benchmark/060919_static_Python.npy' 
Jun19_npyFile = np.load(Jun19_npy)
plot_np(Jun19_npyFile[2,0:1000])

Jun19_Labviewtxt = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/June2019_Benchmark/060919_static_Labview.txt' 
Jun19_LabviewFile = convert_to_np_labview(Jun19_Labviewtxt)
plot_np(Jun19_LabviewFile[5,:,2])

Mar19_Labviewtxt = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/June2019_Benchmark/033019_static_Labview.txt' 
Mar19_LabviewFile = convert_to_np_labview(Mar19_Labviewtxt)
plot_np(Mar19_LabviewFile[5,:,2])
