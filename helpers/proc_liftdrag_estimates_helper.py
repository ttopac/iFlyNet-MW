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
    cl = lsys.results['Test'].nfres.CL
    cd = lsys.results['Test'].nfres.CDi
    liftdrag_dict[identifier] = [cl, cd]
  else:
    cl = liftdrag_dict[identifier][0]
    cd = liftdrag_dict[identifier][1]


  lift = 1/2 * const.RHO * airspeed**2 * cl * const.CHORD * const.SPAN #Newtons
  drag = 1/2 * const.RHO * airspeed**2 * cd * const.CHORD * const.SPAN #Newtons
  return lift, drag