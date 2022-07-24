import sys
import os
sys.path.append(os.path.abspath('./fbf-vlm'))
import tornadocoeff
import constant as const

def get_liftANDdrag(liftdrag_dict, airspeed, alpha, mfc1, mfc2):
  state_list = [airspeed, alpha, mfc1, mfc2]
  identifier = ""
  for item in state_list:
    identifier += str(item)
  
  if identifier not in liftdrag_dict:
    lsys = tornadocoeff.return_results(airspeed, alpha, mfc1, mfc2)
    if airspeed == 0:
      cl = 0
      cdi = 0
    else:
      cl = lsys.results['Test'].nfres.CL
      cdi = lsys.results['Test'].nfres.CDi
    liftdrag_dict[identifier] = [cl, cdi]
  else:
    cl = liftdrag_dict[identifier][0]
    cdi = liftdrag_dict[identifier][1]

  lift = 1/2 * const.RHO * airspeed**2 * cl * const.CHORD * const.SPAN #Newtons
  drag_i = 1/2 * const.RHO * airspeed**2 * cdi * const.CHORD * const.SPAN #Newtons
  return lift, drag_i, liftdrag_dict