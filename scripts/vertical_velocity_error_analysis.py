# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 16:27:36 2014

@author: jc3e13
"""

import numpy as np
import matplotlib.pyplot as plt
import emapex

try:

    print("Floats {} and {}.".format(E76.floatID, E77.floatID))

except NameError:

    E76 = emapex.EMApexFloat('../../data/EM-APEX/allprofs11.mat', 4976)
    E76.apply_w_model('../../data/EM-APEX/4976_fix_p0k0M_fit_info.p')
    E76.apply_strain('../../data/EM-APEX/4976_N2_ref_300dbar.p')
    E76.apply_isopycnal_displacement('../../data/EM-APEX/srho_4976_100mbin.p')

    E77 = emapex.EMApexFloat('../../data/EM-APEX/allprofs11.mat', 4977)
    E77.apply_w_model('../../data/EM-APEX/4977_fix_p0k0M_fit_info.p')
    E77.apply_strain('../../data/EM-APEX/4977_N2_ref_300dbar.p')
    E77.apply_isopycnal_displacement('../../data/EM-APEX/srho_4977_100mbin.p')