import sys
import os
from multiprocessing import Queue
import pathlib
from tkinter import Tk, Button
from tkinter import S
import tensorflow.keras
import keras_resnet
import keras_resnet.models
import numpy as np

sys.path.append(os.path.abspath('./helpers'))
import gui_windows_helper
import procoffline_helper
import streamdata_helper
import digitize_airspeed_helper
import digitize_aoa_helper

INCLUDE_AIRSPEED_TRUTH = False
INCLUDE_AOA_TRUTH = False

INCLUDE_STALL_EST = True
INCLUDE_LIFTDRAG_EST = True
INCLUDE_MFC_EST = True
INCLUDE_STATE_EST = True
INCLUDE_LIFTDRAG_EST_WOCOMPARISON = False
INCLUDE_WING_CARTOON = True

INCLUDE_AIRSPEED_COMPARISON_PLOT = True
INCLUDE_AOA_COMPARISON_PLOT = True
INCLUDE_LIFTDRAG_COMPARISON_PLOT = True

#Choose GUI_TYPE between
#"cartoon", "signal only", "signal with MFC", "MFC with stall and lift/drag", "MFC with all state"
GUI_TYPE = "cartoon"

file_path = pathlib.Path(__file__).parent.absolute()
# main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# main_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/Macintosh HD/Users/tanay/GoogleDrive/Team Drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
MAIN_FOLDER = '/Volumes/GoogleDrive-109082130355562393140/Shared drives/WindTunnelTests-Feb2019/July2022_Tests_SNIC/'
TEST_LOC = 'Offline_Tests/offline3_July6/'
MODELS_LOC = 'Kerasfiles_Dec2020/'
test_folder = os.path.join(MAIN_FOLDER, TEST_LOC)
models_folder = os.path.join(MAIN_FOLDER, MODELS_LOC)

models = dict()
models['types'] = ['stall', 'liftdrag', 'state']
models['filenames'] = ['stall_9sensors_train991_val994', 'reg_7sensors_train0020_val0022', 'state_9sensors_train992_val972']
models['activesensors'] = [(0, 1, 2, 3, 4, 5, 6, 14, 15), (0, 1, 2, 3, 4, 5, 6), (0, 1, 2, 3, 4, 5, 6, 14, 15)] #For regression, last 2 sensors give ground truth.
models['modelfiles'] = list()
models['means'] = np.array([-4.334589129779109e-06, 8.410618468135621e-05, 0.0003380918816729708, -0.00033040819902024725, -0.0004918243008301694, -0.00011952919733986609, -88.5091598596475, 0, 0, 0, 0, 0, 0, 0, -149.31235739451475, -1.4116125522601457, 0, 0])
models['stddevs'] = np.array([0.0011386681293641748, 0.0016901989191845132, 0.0012115932943635751, 0.0015570071919707178, 0.0012676181753638542, 0.0012784967994997837, 50.90707044913575, 0, 0, 0, 0, 0, 0, 0, 137.46263891169286, 39.068130385665526, 0, 0])
params = dict()
params ['sample_rate'] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 

def start_offline_button(gui_app, queue):
  startoffline_button = Button(gui_app.parent, text='Click to start the stream...', command=lambda : queue.put(False))
  startoffline_button.grid(row=0, column=0, rowspan=1, columnspan=8, sticky=S)

if __name__ == '__main__':
  #Define parameters
  VISIBLE_DURATION = 30 #seconds
  PLOT_REFRESH_RATE = 0.1 #seconds. This should be equal to or slower than 30hz (equal to or more than 0.033)
  KERAS_SAMPLESIZE=233 #This is also used for pred_freq. Bad naming here.
  DOWNSAMPLE_MULT = KERAS_SAMPLESIZE #For this app these two are  equal to have equal number of lift/drag values.
  USE_COMPENSATED_STRAINS = True
  MFC_ESTIMATE_METH = 'simple' #simple or full
  LIFTDRAG_ESTIMATE_METH = '1dcnn'

  ###
  #Load the data and models
  ###
  leakyrelu = tensorflow.keras.layers.LeakyReLU(alpha=0.02)
  resnet_model = keras_resnet.models.ResNet1D18(freeze_bn=True)
  resnet_bn_layer = keras_resnet.layers.BatchNormalization(freeze=True)
  test_data = np.load(os.path.join(test_folder,'test.npy')) #(18, ~2000000) channels: PZT1, PZT2, PZT3, PZT4, PZT5, PZT6, SG1, SG2, SG3, SG4, SG5, SG6, SG7, SG9, Lift, Drag, SG1RTD, WingRTD
  stepcount = int (test_data.shape[1] / params ['sample_rate'] / PLOT_REFRESH_RATE) + 1
  models['filepaths'] = list(map(lambda x: models_folder+f'{x}', models['filenames']))
  for filepath in models['filepaths']:
    if os.path.isfile(filepath+'.hdf5'): #Old format saved with weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.hdf5', custom_objects={'LeakyReLU': leakyrelu, 'ResNet1D18':resnet_model, 'BatchNormalization':resnet_bn_layer}))
    elif os.path.isfile(filepath+'.tf'): #New format saved without weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.tf', custom_objects={'LeakyReLU': leakyrelu, 'ResNet1D18':resnet_model, 'BatchNormalization':resnet_bn_layer}))
      models['modelfiles'][-1].load_weights(os.path.join(filepath,'.ckpt'))
    else:
      raise Exception ('Problem with loading Keras models')

  ###
  #Process i-FlyNet estimations. Either make new estimations and save or use cached ones.
  #All estimates are of size "stepcount".
  ###
  estimates = procoffline_helper.ProcEstimatesOffline(test_data, params['sample_rate'], PLOT_REFRESH_RATE, DOWNSAMPLE_MULT, USE_COMPENSATED_STRAINS, models, KERAS_SAMPLESIZE)
  estimates_path = os.path.join(test_folder, "saved_estimates"+"_"+MFC_ESTIMATE_METH+"_"+LIFTDRAG_ESTIMATE_METH)
  if not os.path.isdir(estimates_path): #Create a folder to put estimates if it doesn't already exists
    os.mkdir(estimates_path)
  if len(os.listdir(estimates_path)) < 4:  #All estimations are not there.
    #Make estimates
    estimates.make_estimates(True, True, True, MFC_ESTIMATE_METH, LIFTDRAG_ESTIMATE_METH)
    #Save estimate files for easy reuse.
    np.save(os.path.join(estimates_path,'stall_estimates.npy'), estimates.stall_estimates)
    np.save(os.path.join(estimates_path,'state_estimates.npy'), estimates.state_estimates)
    np.save(os.path.join(estimates_path,'liftdrag_estimates.npy'), estimates.liftdrag_estimates)
    np.save(os.path.join(estimates_path,'mfc_estimates.npy'), estimates.mfc_estimates)
  else:
    #Load estimate files for reuse.
    estimates.stall_estimates = np.load(os.path.join(estimates_path,'stall_estimates.npy'))
    estimates.state_estimates = np.load(os.path.join(estimates_path,'state_estimates.npy'))
    estimates.liftdrag_estimates = np.load(os.path.join(estimates_path,'liftdrag_estimates.npy'))
    estimates.mfc_estimates = np.load(os.path.join(estimates_path,'mfc_estimates.npy'))

  ###
  #Process ground truth videos:
  ###
  truth_digitizations_path = os.path.join(test_folder, "saved_digitizations")
  if INCLUDE_AIRSPEED_TRUTH:
    if os.path.exists(os.path.join(truth_digitizations_path,"airspeed_digitized.npy")):
      ys_airspeed = np.load(os.path.join(truth_digitizations_path,'airspeed_digitized.npy'))
    else:
      airspeed_vid_path = os.path.join(test_folder, "anemometer.mp4")
      ys_airspeed = digitize_airspeed_helper.digitize_airspeed(airspeed_vid_path)
      np.save(os.path.join(truth_digitizations_path,'airspeed_digitized.npy'), ys_airspeed, allow_pickle=True)
  if INCLUDE_AOA_TRUTH:
    if os.path.exists(os.path.join(truth_digitizations_path,"aoa_digitized.npy")):
      ys_aoa = np.load(os.path.join(truth_digitizations_path,'aoa_digitized.npy'))
    else:
      aoa_csv_path = os.path.join(test_folder, "aoa_hist.csv")
      ys_aoa = digitize_aoa_helper.digitize_aoa(aoa_csv_path)
      np.save(os.path.join(truth_digitizations_path,'aoa_digitized.npy'), ys_aoa, allow_pickle=True)

  ###
  #Initiate the streams of camera + measurements + estimations and place them on the GUI
  ###
  root = Tk()
  root.title ("Offline i-FlyNet")
  video_labels = ("Experiment Cam", "Disabled")
  TITLE_LABEL = "Flight Characteristics"
  camnums = ('2_deframed', '2_deframed')

  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(root, PLOT_REFRESH_RATE, DOWNSAMPLE_MULT, True, LIFTDRAG_ESTIMATE_METH)
  GUIapp.draw_midrow(TITLE_LABEL, os.path.join(file_path.parent, 'assets', 'legend.png'))
  GUIapp.draw_cartoon_cvs(os.path.join(file_path.parent, 'assets'))
  GUIapp.initialize_queues_or_lists()

  ###
  #Get data for GUI
  ###
  data_cut = int (params['sample_rate'] * PLOT_REFRESH_RATE)
  for i in range(stepcount): #(3001 for 300second of data with 10hz refresh rate)
    relev_data = test_data[:, i*data_cut : (i+1)*data_cut]
    red_relev_data = np.mean(relev_data, axis=1)

    GUIapp.data_list.append(red_relev_data)
    GUIapp.stallest_list.append(estimates.stall_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.stateest_list.append(estimates.state_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.liftdragest_list.append(estimates.liftdrag_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.shape_list.append(estimates.mfc_estimates[int(estimates.pred_count/stepcount*i)])

    if INCLUDE_AIRSPEED_TRUTH:
      GUIapp.meas_airspeed_list.append(ys_airspeed[round(i/(1/PLOT_REFRESH_RATE))])
    else:
      GUIapp.meas_airspeed_list.append(-1)

    if INCLUDE_AOA_TRUTH:
      GUIapp.meas_aoa_list.append(ys_aoa[round(i/(1/PLOT_REFRESH_RATE))])
    else:
      GUIapp.meas_aoa_list.append(-1)

  ###
  #Finalize the GUI and start streaming.
  ###
  streamhold_queue = Queue()
  stream = streamdata_helper.StreamOffline(GUIapp, params, streamhold_queue, test_folder, USE_COMPENSATED_STRAINS, DOWNSAMPLE_MULT, VISIBLE_DURATION, PLOT_REFRESH_RATE)
  stream.initialize_video(video_labels, camnums)

  stream.initialize_estimates(INCLUDE_STALL_EST,
                              INCLUDE_LIFTDRAG_EST,
                              INCLUDE_MFC_EST,
                              INCLUDE_STATE_EST,
                              INCLUDE_LIFTDRAG_EST_WOCOMPARISON,
                              INCLUDE_WING_CARTOON)
  stream.initialize_plots_wcomparison(INCLUDE_AIRSPEED_COMPARISON_PLOT, 
                                      INCLUDE_AOA_COMPARISON_PLOT,
                                      INCLUDE_LIFTDRAG_COMPARISON_PLOT)
  GUIapp.place_on_grid(GUI_TYPE, INCLUDE_LIFTDRAG_COMPARISON_PLOT)


  #Run the GUI
  start_offline_button(GUIapp, streamhold_queue)
  root.mainloop()