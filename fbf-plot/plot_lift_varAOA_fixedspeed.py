import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.abspath('./helpers'))
import proc_tempcomp_helper

vels = [6,8,10,12,14,16,18,20]
aoa = [0,2,4,6,8,10,12,14,16,17,18,19,20,'0_2']
test_len = 1 #minutes
# test_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# test_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# test_folder = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
test_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/Training_Tests/train4_Dec14/'

#Get reference temperature points
reftemp_vels = list()
ref_temps = list()
for file in os.listdir(test_folder):
  if file.startswith("reftemps"):
    vel_str = file.split('_')[2][:-2]
    reftemp_vels.append(int(vel_str))
    ref_temps.append(np.load(test_folder+file).tolist())

for vel in vels:
  #Create empty lists that will store temperature values:
  sum_PZT1 = list()
  ave_SG1 = list()
  ave_SG1_comp = list()
  ave_lift = list()
  ave_lift_comp = list()

  #Span the angle range
  for i in range(len(aoa)):
    trainData = np.load(test_folder+'train_{}ms_{}deg_{}min.npy'.format(vel, aoa[i], test_len))
    sum_PZT1.append(np.mean(np.sum(trainData[1]**2)))
    ave_SG1.append(np.mean(-trainData[6])) #6 is SG1 at root.
    ave_lift.append(np.mean(-trainData[14])) #14 is Lift CommSG

    #Handle temperature compensation
    if vel in reftemp_vels:
      index = reftemp_vels.index(vel)
    else:
      closest_val = np.asarray(reftemp_vels)[np.asarray(reftemp_vels) < vel].max() #Gets the maximum temp_reset_vel smaller than vel
      index = reftemp_vels.index(closest_val)
    ref_temp_SG1 = ref_temps[index][0]
    ref_temp_wing = ref_temps[index][1]

    #SG1 temp. comp.
    SSNSG_temp_comp = proc_tempcomp_helper.SSNSG_Temp_Comp(ref_temp_SG1, ref_temp_wing)
    comp_SSNSG = SSNSG_temp_comp.compensate(trainData[6], trainData[16], 'SG1', 119)
    ave_SG1_comp.append (np.mean(-comp_SSNSG))

    #CommSG temp. comp.
    commSG_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(ref_temp_SG1, ref_temp_wing)
    comp_commSG, comp_commSG_var = commSG_temp_comp.compensate(trainData[14], trainData[17], 'rod', 0)
    ave_lift_comp.append (np.mean(-comp_commSG))

  fig = plt.figure(figsize=(6.0, 8.0))
  ax1 = fig.add_subplot(3,1,1)
  ax2 = fig.add_subplot(3,1,2)
  ax3 = fig.add_subplot(3,1,3)
  ax1.set_title("Sum of PZT1 signals".format(vel), fontsize=12)
  ax1.set_xlabel("Angle (deg)", fontsize=11)
  ax1.set_ylabel("Voltage (V)", fontsize=11)
  ax2.set_title("-SG1 readings for V = {}m/s".format(vel), fontsize=12)
  ax2.set_xlabel("Angle (deg)", fontsize=11)
  ax2.set_ylabel("Microstrain (ue)", fontsize=11)
  ax3.set_title("-SG Lift for V = {}m/s".format(vel), fontsize=12)
  ax3.set_xlabel("Angle (deg)", fontsize=11)
  ax3.set_ylabel("Microstrain (ue)", fontsize=11)


  ax1.plot(aoa[:-1], sum_PZT1[:-1], '.-', linewidth=0.5, label="PZT1")
  ax1.scatter(0, sum_PZT1[-1], marker='*', c='red', label="PZT1 0_2")
  ax2.plot(aoa[:-1], ave_SG1[:-1], '.-', linewidth=0.5, label="-SG1")
  ax2.plot(aoa[:-1], ave_SG1_comp[:-1], '.:', color=ax1.lines[0].get_color(), linewidth=0.5, label="-SG1 (comp.)")
  ax2.scatter(0, ave_SG1_comp[-1], marker='*', c='red', label="-SG1 (comp.) 0_2")
  ax3.plot(aoa[:-1], ave_lift[:-1], '.-', linewidth=0.5, label="SG Lift")
  ax3.plot(aoa[:-1], ave_lift_comp[:-1], '.:', color=ax2.lines[0].get_color(), linewidth=0.5, label="SG Lift (comp.)")
  ax3.scatter(0, ave_lift_comp[-1], marker='*', c='red', label="SG Lift (comp.) 0_2")

  ax1.legend(fontsize=7, loc="upper left", ncol=1, columnspacing=1)
  ax2.legend(fontsize=7, loc="lower left", ncol=1, columnspacing=1)
  ax3.legend(fontsize=7, loc="upper left", ncol=1, columnspacing=1)

  ax1.set_xticks(aoa[:-1][::4])
  ax2.set_xticks(aoa[:-1][::4])
  ax3.set_xticks(aoa[:-1][::4])
  plt.tight_layout(pad=2.0)
  # plt.savefig(test_folder+'{}ms_varAoA.png'.format(vel))
  # plt.show()