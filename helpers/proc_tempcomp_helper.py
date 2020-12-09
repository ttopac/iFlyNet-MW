import numpy as np

#Comm. SG compensation parameters for Sept2020 tests (for Aluminum) (Dec 7, 2020)
poly_coeffs = (-59, 3.39, -6.03E-2, 4.09E-4, -6.42E-7)
gage_fact, k_poly = 2.06, 2

#SSN SG compensation parameters for Sept2020 tests (skipping SG8)
r_total = np.asarray ([14, 14.4, 14.1, 15.3, 14.7, 14, 14.3, 13.9])
r_wire = np.asarray ([0.65, 0.6, 0.65, 1.3, 0, 0.2, 0.5, 0.2]) #Values from Sept16. From Xiyuan: [0.4, 0.6, 0.3, 1.5, 0.9, 0.2, 0.5, 0.1]
# r_wire = np.asarray ([0.2, 0.2, 0.3, 1.1, 0.2, 0.2, 0.5, 0.1]) #Approx from drift8_Sept15_0_3 test.
alpha_gold = 1857.5
alpha_constantan = 21.758

class CommSG_Temp_Comp():
  def __init__ (self, ref_temp_SG1, ref_temp_wing):
    self.gage_fact = gage_fact
    self.k_poly = k_poly
    self.poly_coeffs = poly_coeffs
    self.ref_temp_SG1 = ref_temp_SG1
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
    ref_temp = self.ref_temp_SG1 if SG_surf == 'SG1' else self.ref_temp_wing
    e_therm = self.poly_coeffs[0] + self.poly_coeffs[1]*temp + self.poly_coeffs[2]*temp**2 + self.poly_coeffs[3]*temp**3 + self.poly_coeffs[4]*temp**4
    e_therm_ref = self.poly_coeffs[0] + self.poly_coeffs[1]*ref_temp + self.poly_coeffs[2]*ref_temp**2 + self.poly_coeffs[3]*ref_temp**3 + self.poly_coeffs[4]*ref_temp**4
    return (e_therm, e_therm_ref)

  def comp_matl_dev (self, temp, SG_surf, commSG_CTEvar):
    ref_temp = self.ref_temp_SG1 if SG_surf == 'SG1' else self.ref_temp_wing
    return (commSG_CTEvar)*(temp - ref_temp)

  def compensate (self, readings, temp, SG_surf, commSG_CTEvar):
    e_therm, e_therm_ref = self.comp_al(temp, SG_surf)
    corr_matl_dev = 0
    if np.absolute(commSG_CTEvar)*1E6 > 1:
      corr_matl_dev = self.comp_matl_dev(temp, SG_surf, commSG_CTEvar)
    e_substrate = readings - ((e_therm - e_therm_ref)*self.k_poly/self.gage_fact) - corr_matl_dev
    return (e_substrate, 0)

  
class SSNSG_Temp_Comp():
  def __init__ (self, ref_temp_SG1, ref_temp_wing):
    self.ref_temp_SG1 = ref_temp_SG1
    self.ref_temp_wing = ref_temp_wing

  def compensate (self, readings, temp, SG_surf, SSNSG_CTEvar):
    ref_temp = self.ref_temp_SG1 if SG_surf == 'SG1' else self.ref_temp_wing
    e_therm = (SSNSG_CTEvar)*(temp - ref_temp)
    e_substrate = readings - e_therm
    return e_substrate