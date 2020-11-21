import numpy as np

#Comm. SG compensation parameters for Sept2020 tests (for steel)
# poly_coeffs = (-23.65, 2.06, -5.02E-2, 2.26E-4, 0.3, 0.219)
# poly_coeffs_newchar = [17.14, -8.573, 0.4876, -0.004384, 0, 0] #Only tempup part
# gage_fact, k_poly = 2, 2
# gage_fact_CTE, SG_matl_CTE = 93E-6, 10.8E-6
# al6061_CTE = 23.6E-6

#Comm. SG compensation parameters for Sept2020 tests (for Aluminum) (Nov 20, 2020)
poly_coeffs = (-59, 3.39, -6.03E-2, 4.09E-4, -6.42E-7)
gage_fact, k_poly = 2.06, 2

#SSN SG compensation parameters for Sept2020 tests (skipping SG8)
r_total = np.asarray ([14, 14.4, 14.1, 15.3, 14.7, 14, 14.3, 13.9])
r_wire = np.asarray ([0.65, 0.6, 0.65, 1.3, 0, 0.2, 0.5, 0.2]) #Values from Sept16. From Xiyuan: [0.4, 0.6, 0.3, 1.5, 0.9, 0.2, 0.5, 0.1]
# r_wire = np.asarray ([0.2, 0.2, 0.3, 1.1, 0.2, 0.2, 0.5, 0.1]) #Approx from drift8_Sept15_0_3 test.
alpha_gold = 1857.5
alpha_constantan = 21.758

class CommSG_Temp_Comp():
  def __init__ (self, ref_temp_rod, ref_temp_wing):
    self.gage_fact = gage_fact
    self.k_poly = k_poly
    self.poly_coeffs = poly_coeffs
    self.ref_temp_rod = ref_temp_rod
    self.ref_temp_wing = ref_temp_wing

  def comp_steel (self, temp):
    # e_therm = self.poly_coeffs[0] + self.poly_coeffs[1]*temp + self.poly_coeffs[2]*temp**2 + self.poly_coeffs[3]*temp**3
    # e_therm_ref = self.poly_coeffs[0] + self.poly_coeffs[1]*self.ref_temp + self.poly_coeffs[2]*self.ref_temp**2 + self.poly_coeffs[3]*self.ref_temp**3
    # e_therm_lead = (temp-20) * self.poly_coeffs[5]
    # e_therm_lead_ref = (self.ref_temp-20) * self.poly_coeffs[5]
    # uncert = (temp - 20) * self.poly_coeffs[4]
    # return (e_therm, e_therm_ref, e_therm_lead, e_therm_lead_ref, uncert)
    pass #Code not updated for steel

  def comp_al (self, temp, SG_surf):
    ref_temp = self.ref_temp_rod if SG_surf == 'rod' else self.ref_temp_wing
    e_therm = self.poly_coeffs[0] + self.poly_coeffs[1]*temp + self.poly_coeffs[2]*temp**2 + self.poly_coeffs[3]*temp**3 + self.poly_coeffs[4]*temp**4
    e_therm_ref = self.poly_coeffs[0] + self.poly_coeffs[1]*ref_temp + self.poly_coeffs[2]*ref_temp**2 + self.poly_coeffs[3]*ref_temp**3 + self.poly_coeffs[4]*ref_temp**4
    return (e_therm, e_therm_ref)

  def comp_matl_dev (self, temp, SG_surf, SG_STC_CTE, subs_matl_CTE):
    ref_temp = self.ref_temp_rod if SG_surf == 'rod' else self.ref_temp_wing
    return (subs_matl_CTE - SG_STC_CTE)*(temp - ref_temp)*1E6

  def compensate (self, readings, temp, SG_surf, SG_STC_CTE, subs_matl_CTE):
    e_therm, e_therm_ref = self.comp_al(temp, SG_surf)
    corr_matl_dev = 0
    if np.absolute(subs_matl_CTE-SG_STC_CTE)*1E6 > 1:
      corr_matl_dev = self.comp_matl_dev(temp, SG_surf, SG_STC_CTE, subs_matl_CTE)
    e_substrate = readings - ((e_therm - e_therm_ref)*self.k_poly/self.gage_fact) - corr_matl_dev
    return (e_substrate, 0)

  
class SSNSG_Temp_Comp():
  def __init__ (self, ref_temp):
    self.ref_temp = ref_temp
    self.r_total = r_total
    self.r_wire = r_wire
    self.alpha_gold = alpha_gold
    self.alpha_constantan = alpha_constantan

  def compensate (self, readings, temp):
    r_ratio = self.r_wire / self.r_total
    e_therm = r_ratio*self.alpha_gold + (1-r_ratio)*self.alpha_constantan
    e_substrate = readings - e_therm.reshape(-1,1)*(temp-self.ref_temp)
    return e_substrate