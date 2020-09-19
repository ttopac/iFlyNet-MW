class CommSG_Temp_Comp():
  def __init__ (self, poly_coeffs, gage_fact_CTE, SG_matl_CTE, substrate_matl_CTE, ref_temp, ownchar, gage_fact=2, k_poly=2):
    self.poly_coeffs = poly_coeffs
    self.gage_fact_CTE = gage_fact_CTE
    self.gage_fact = gage_fact
    self.k_poly = k_poly
    self.SG_matl_CTE = SG_matl_CTE
    self.substrate_matl_CTE = substrate_matl_CTE
    self.ref_temp = ref_temp
    self.ownchar = ownchar

  def comp_steel (self, temp):
    e_therm = self.poly_coeffs[0] + self.poly_coeffs[1]*temp + self.poly_coeffs[2]*temp**2 + self.poly_coeffs[3]*temp**3
    e_therm_ref = self.poly_coeffs[0] + self.poly_coeffs[1]*self.ref_temp + self.poly_coeffs[2]*self.ref_temp**2 + self.poly_coeffs[3]*self.ref_temp**3
    e_therm_lead = (temp-20) * self.poly_coeffs[5]
    e_therm_lead_ref = (self.ref_temp-20) * self.poly_coeffs[5]
    uncert = (temp - 20) * self.poly_coeffs[4]
    return (e_therm, e_therm_ref, e_therm_lead, e_therm_lead_ref, uncert)

  def correct_gage_fact (self, temp):
    return self.gage_fact + self.gage_fact_CTE*(temp - self.ref_temp)

  def comp_matl_dev (self, temp):
    return (self.substrate_matl_CTE - self.SG_matl_CTE)*(temp - self.ref_temp)*1E6

  def compensate (self, readings, temp):
    if self.ownchar:
      e_therm, e_therm_ref, e_therm_lead, e_therm_lead_ref, uncert = self.comp_steel(temp)
      e_substrate = readings - ((e_therm - e_therm_ref)*self.k_poly/self.gage_fact) 
    else:
      e_therm, e_therm_ref, e_therm_lead, e_therm_lead_ref, uncert = self.comp_steel(temp)
      corr_matl_dev = self.comp_matl_dev(temp)
      e_steel = readings - ((e_therm - e_therm_ref)*self.k_poly/self.gage_fact) - (e_therm_lead - e_therm_lead_ref)
      e_substrate = e_steel - corr_matl_dev
    return (e_substrate, uncert)

  
class SSNSG_Temp_Comp():
  def __init__ (self, ref_temp, r_total, r_wire, alpha_gold, alpha_constantan):
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