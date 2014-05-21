# -*- coding: utf-8 -*-
"""
Created on Tue May 20 15:45:36 2014

A place for finescale parameterisation functions.

@author: jc3e13
"""

import numpy as np
import gsw


def adiabatic_level(P, SA, T, N2, lat, P_bin_width=200., deg=1):
    """Generate smooth buoyancy frequency profile by applying the adiabatic
    levelling method of Bray and Fofonoff (1981).

    TODO: Add optional parameter ignore_above.

      Parameters
      ----------
      P : 1-D ndarray
          Pressure [dbar]
      SA : 1-D ndarray
          Absolute salinity [g/kg]
      T : 1-D ndarray
          Temperature [degrees C]
      N2 : 1-D ndarray
          Buoyancy frequency [s-2]
      lat : float
          Latitude [-90...+90]
      p_bin_width : float, optional
          Pressure bin width [dbar]
      deg : int, option
          Degree of polynomial fit.

      Returns
      -------
      N2_ref : 1-D ndarray of floats
          Reference buoyancy frequency [s-2]

      Raises
      ------

      Notes
      -----

      Examples
      --------

    """

    N2_ref = np.NaN*P.copy()
    P_min, P_max = np.nanmin(P), np.nanmax(P)
    pot_rho = gsw.pot_rho_t_exact

    for i in xrange(len(P)):
        P_bin_min = np.maximum(P[i] - P_bin_width/2., P_min)
        P_bin_max = np.minimum(P[i] + P_bin_width/2., P_max)
        in_bin = np.where((P >= P_bin_min) & (P <= P_bin_max))[0]
        if in_bin.size == 0:
            continue
        P_bar = np.nanmean(P[in_bin])
        T_bar = np.nanmean(T[in_bin])
        SA_bar = np.nanmean(SA[in_bin])
        rho_bar = pot_rho(SA_bar, T_bar, P_bar, P_bar)
        sv = 1./pot_rho(SA[in_bin], T[in_bin], P[in_bin], P_bar)

        p = np.polyfit(P[in_bin], sv - np.nanmean(sv), deg)
        g = gsw.grav(lat, P_bar)
        N2_ref[i] = -1e-4 * rho_bar**2 * g**2 * p[0]

    return N2_ref
