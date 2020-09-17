import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.abspath('./helpers'))
import proc_tempcomp_helper

#Comm. SG compensation parameters
poly_coeffs = (-23.65, 2.06, -5.02E-2, 2.26E-4, 0.3, 0.219)
gage_fact, k_poly = 2, 2
gage_fact_CTE, SG_matl_CTE = 93E-6, 10.8E-6
al6061_CTE = 23.6E-6

#SSN SG compensation parameters (skipping SG8)
r_total = np.asarray ([14, 14.4, 14.1, 15.3, 14.7, 14, 14.3, 13.9])
r_wire = np.asarray ([0.65, 0.6, 0.65, 1.3, 0, 0.2, 0.5, 0.2]) #Values from Sept16. From Xiyuan: [0.4, 0.6, 0.3, 1.5, 0.9, 0.2, 0.5, 0.1]alpha_gold = 1857.5
alpha_gold = 1857.5
alpha_constantan = 21.758

#Creare empty lists that will store temperature values:
init_temps = [20.2181, 22.9226] #This is 20.2181 for V=[2-12] and 22.9226 for V=[14-20]
ave_SG1 = list()
ave_SG1_comp = list()
ave_lift = list()
ave_lift_comp = list()

# vel = input ("Enter the vel to plot: ")
# aoa = input ("Enter the aoa to plot: ")
vel = 10
aoa = [0,2,4,6,8,10,12,14,16,17,18,19,20]

for a in aoa:
  # trainData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/')
  trainData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/train2_Sept16/train_{}ms_{}deg.npy'.format(vel,a))
  ave_SG1.append(np.mean(-trainData[6])) #6 is SG1 at root.
  ave_lift.append(np.mean(-trainData[14])) #14 is Lift CommSG

  #Handle temperature compensation
  ref_temp = init_temps[0] if vel<=12 else init_temps[1]
  #SG1 temp. comp.
  SSNSG_temp_comp = proc_tempcomp_helper.SSNSG_Temp_Comp(ref_temp, r_total, r_wire, alpha_gold, alpha_constantan)
  comp_SSNSG = SSNSG_temp_comp.compensate(trainData[6:14], trainData[16])
  ave_SG1_comp.append (np.mean(-comp_SSNSG[0]))

  #CommSG temp. comp.
  commSG_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(poly_coeffs, gage_fact_CTE, SG_matl_CTE, al6061_CTE, ref_temp, gage_fact, k_poly)
  comp_commSG, comp_commSG_var = commSG_temp_comp.compensate(trainData[14:16], trainData[16])
  ave_lift_comp.append (np.mean(-comp_commSG[0]))

fig = plt.figure(figsize=(6.0, 6.0))
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
ax1.set_title("-SG1 readings for V = {}m/s".format(vel), fontsize=12)
ax1.set_xlabel("Angle (deg)", fontsize=11)
ax1.set_ylabel("Microstrain (ue)", fontsize=11)
ax2.set_title("-SG Lift for V = {}m/s".format(vel), fontsize=12)
ax2.set_xlabel("Angle (deg)", fontsize=11)
ax2.set_ylabel("Microstrain (ue)", fontsize=11)

ax1.plot(aoa, ave_SG1, '-', linewidth=0.5, label="-SG1")
ax1.plot(aoa, ave_SG1_comp, ':', color=ax1.lines[0].get_color(), linewidth=0.5, label="-SG1 (compensated)")
ax2.plot(aoa, ave_lift, '-', linewidth=0.5, label="SG Lift")
ax2.plot(aoa, ave_lift_comp, ':', color=ax2.lines[0].get_color(), linewidth=0.5, label="SG Lift (compensated)")
plt.tight_layout(pad=2.0)
plt.show()