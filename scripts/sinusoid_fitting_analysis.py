# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 16:20:33 2014

@author: jc3e13
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# from matplotlib.colors import LogNorm
# from matplotlib.ticker import LogFormatterMathtext
import datetime
import gsw
import os
import sys
import glob
import scipy.signal as sig
import scipy.optimize as op
from scipy.integrate import cumtrapz, odeint
from scipy.interpolate import griddata

lib_path = os.path.abspath('../python')
if lib_path not in sys.path:
    sys.path.append(lib_path)

import sandwell
import utils
import emapex
import plotting_functions as pf
import gravity_waves as gw

try:
    print("Floats {} and {} exist!".format(E76.floatID, E77.floatID))
except NameError:
    E76 = emapex.EMApexFloat('../../data/EM-APEX/allprofs11.mat', 4976)
    E76.apply_w_model('../../data/EM-APEX/4976_fix_p0k0M_fit_info.p')
    E76.apply_strain('../../data/EM-APEX/4976_N2_ref_300dbar.p')
    E76.apply_isopycnal_displacement('../../data/EM-APEX/srho_4976_100mbin.p')
    E77 = emapex.EMApexFloat('../../data/EM-APEX/allprofs11.mat', 4977)
    E77.apply_w_model('../../data/EM-APEX/4977_fix_p0k0M_fit_info.p')
    E77.apply_strain('../../data/EM-APEX/4977_N2_ref_300dbar.p')
    E77.apply_isopycnal_displacement('../../data/EM-APEX/srho_4977_100mbin.p')


# %% Script params.

# Bathymetry file path.
bf = os.path.abspath(glob.glob('../../data/sandwell_bathymetry/topo_*.img')[0])
# Figure save path.
sdir = '../figures/sinusoid_fitting_analysis'
# Universal figure font size.
matplotlib.rc('font', **{'size': 7})

# %% Spectral analysis

def plane_wave(x, A, k, phase):
    return A*np.cos((k*x + phase))

E76_hpids = np.arange(27, 34)
E77_hpids = np.arange(23, 30)

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    for pfl in Float.get_profiles(hpids):

        z = getattr(pfl, 'z')
        Ww = getattr(pfl, 'Ww')

        # Remove nans and the top 50 m.
        nans = np.isnan(z) | np.isnan(Ww) | (z > -50)
        z, Ww = z[~nans], Ww[~nans]

        # Setting up the spectral analysis.
        dz = np.abs(np.round(np.mean(np.diff(z))))
        dk = 1./dz
        iz = np.arange(np.min(z), np.max(z), dz)
        idxs = np.argsort(z)
        iWw = np.interp(iz, z[idxs], Ww[idxs])
        diWw = sig.detrend(iWw)

        # Doing the spectral analysis.
        m, Pw = sig.welch(iWw, fs=dk, detrend='linear')

        # Try fitting plane wave.
        popt, __ = op.curve_fit(plane_wave, iz, iWw,
                                p0=[0.1, 0.02, 0.])
        mfit = popt[1]/(2.*np.pi)

        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        plt.plot(iWw, iz, plane_wave(iz, *popt), iz)
        plt.xticks(rotation=45)
        plt.xlabel('$W_w$ (m s$^{-1}$)')
        plt.ylabel('$z$ (m)')
        title = ("Float {}, profile {}\nm_fit {:1.1e} m$^{{-1}}$"
                 "\nlambda_fit {:4.0f} m"
                 "").format(Float.floatID, pfl.hpid[0], mfit, 1./mfit)
        plt.title(title)

        plt.subplot(1, 2, 2)
        plt.loglog(m, Pw)
        mmax = m[Pw.argmax()]
        title = ("Float {}, profile {}\nm_max {:1.1e} m$^{{-1}}$"
                 "\nlambda_max {:4.0f} m"
                 "").format(Float.floatID, pfl.hpid, mmax, 1./mmax)
        ylim = plt.ylim()
        plt.plot(2*[mmax], ylim, 'r', 2*[mfit], ylim, 'g')
        plt.title(title)
        plt.xlabel('$m$ (m$^{-1}$)')


# %%

def plane_wave(x, A, k, phase):
    return A*np.cos((k*x + phase))

E76_hpids = np.arange(27, 34)
E77_hpids = np.arange(23, 30)

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    for pfl in Float.get_profiles(hpids):

        z = getattr(pfl, 'z')
        t = getattr(pfl, 'UTC')
        t = 24.*60.*(t - np.nanmin(t))  # Convert to minutes.

        Ww = getattr(pfl, 'Ww')
        N2_ref = getattr(pfl, 'N2_ref')

        nans = np.isnan(z) | np.isnan(t) | np.isnan(Ww) | np.isnan(N2_ref) | (z > -50)
        z, t, Ww, N2_ref = z[~nans], t[~nans], Ww[~nans], N2_ref[~nans]

        # Setting up the spectral analysis.
        ts = 60.*t  # Convert to seconds.
        dt = np.round(np.mean(np.diff(ts)))
        fs = 1./dt
        it = np.arange(np.min(ts), np.max(ts), dt)
        iWw = np.interp(it, ts, Ww)
        diWw = sig.detrend(iWw)

        # Get an idea of the buoyancy frequency.
        N_mean = np.mean(np.sqrt(N2_ref[z < -200]))/(2.*np.pi)
        # The inertial frequency.
        fcor = np.abs(gsw.f(-57.5))/(2.*np.pi)

        # Perform the spectral analysis.
        freqs, Pw = sig.welch(iWw, fs=fs, detrend='linear')

        # Fit a curve.
        popt, __ = op.curve_fit(plane_wave, it, diWw,
                                p0=[0.1, 0.002, 0.])
        omfit = popt[1]/(2.*np.pi)
        period = 1/omfit/60.

        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        plt.plot(diWw, it, plane_wave(it, *popt), it)
        plt.xticks(rotation=45)
        plt.xlabel('$W_w$ (m s$^{-1}$)')
        plt.ylabel('$t$ (s)')
        title = ("Float {}, profile {}\nperiod {} min").format(Float.floatID, pfl.hpid[0], period)
        plt.title(title)

        plt.subplot(1, 2, 2)
        plt.loglog(freqs, Pw)
        ylim = plt.ylim()
        plt.plot(2*[N_mean], ylim, 'r', 2*[fcor], ylim, 'r',  2*[omfit], ylim, 'g')
        plt.title(title)
        plt.xlabel('$f$ (s$^{-1}$)')
        title = ("Float {}, profile {}").format(Float.floatID, pfl.hpid[0])

# %% More complex fitting


def plane_wave2(params, x):
    A, k, m, om, phi = params
    return A*np.cos(k*x[:, 0] + m*x[:, 1] + om*x[:, 2] + phi)


def cost(params, data, func, y):
    return (func(params, data) - y).flatten()

res = []

E76_hpids = np.arange(31, 33)  # np.arange(31, 33)
E77_hpids = np.arange(26, 28)  # np.arange(26, 28)

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    __, idxs = Float.get_profiles(hpids, ret_idxs=True)

    z = Float.z[:, idxs].flatten(order='F')
    x = Float.dist_ctd[:, idxs].flatten(order='F')*1000.
    t = Float.UTC[:, idxs].flatten(order='F')*86400.
    t -= np.nanmin(t)
    W = Float.Ww[:, idxs].flatten(order='F')

    nans = np.isnan(z) | np.isnan(x) | np.isnan(t) | np.isnan(W) | (z > -200)
    data = np.array([x[~nans], z[~nans], t[~nans]]).T
    W = W[~nans]

    x0 = [0.15, 0.004, 0.01, 0.0003, 0.]
    fit = op.leastsq(cost, x0=x0, args=(data, plane_wave2, W))[0]
    print(fit)
    res.append(fit)

    Wm = plane_wave2(fit, data)
    Wm0 = plane_wave2(x0, data)

    plt.figure()
    plt.subplot(3, 1, 1)
    plt.plot(data[:, 0], Wm, data[:, 0], W, data[:, 0], Wm0)
    plt.subplot(3, 1, 2)
    plt.plot(Wm, data[:, 1], W, data[:, 1], Wm0, data[:, 1])
    plt.subplot(3, 1, 3)
    plt.plot(data[:, 2], Wm, data[:, 2], W, data[:, 2], Wm0)


# %%

E76_hpids = np.arange(24, 27)  # np.arange(31, 33)
E77_hpids = np.arange(20, 24)  # np.arange(26, 28)

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    __, idxs = Float.get_profiles(hpids, ret_idxs=True)
    z = Float.z[:, idxs]
    zef = Float.zef[:, idxs]
    U = Float.U_abs[:, idxs]
    N2 = Float.N2_ref[:, idxs]
    nans = np.isnan(z) | np.isnan(N2)
    nansef = np.isnan(zef) | np.isnan(U)
    z, zef, N2, U = z[~nans], zef[~nansef], N2[~nans], U[~nansef]

    U_mean = np.mean(U[zef < -1000.])
    N_mean = np.mean(np.sqrt(N2[z < -200]))
    print("Float {}, U mean: {} m s-1, N mean: {} s-1".format(Float.floatID, U_mean, N_mean))
    print("U/N = {}".format(U_mean/N_mean))

# %% Plots of $W$ with topography

bwr = plt.get_cmap('bwr')
E76_hpids = np.arange(20, 40)  # np.arange(31, 33)
E77_hpids = np.arange(15, 35)  # np.arange(26, 28)
bathy_file = '../../data/sandwell_bathymetry/topo_17.1.img'
vars = ['Ww']  # , 'U_abs', 'V_abs']
zvars = ['z']  # , 'zef', 'zef']
dvars = ['dist_ctd']  # , 'dist_ef', 'dist_ef']
texvars = ['$W_w$']  # , '$U$', '$V$']
clims = [(-10., 10.)]  # , (-100., 100.), (-100, 100.)]

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    __, idxs = Float.get_profiles(hpids, ret_idxs=True)

    for var, zvar, dvar, texvar, clim in zip(vars, zvars, dvars, texvars,
                                             clims):

        V = getattr(Float, var)[:, idxs].flatten(order='F')
        z = getattr(Float, zvar)[:, idxs].flatten(order='F')
        d = getattr(Float, dvar)[:, idxs].flatten(order='F')
        tgps = getattr(Float, 'UTC_start')[idxs]
        lon = getattr(Float, 'lon_start')[idxs]
        lat = getattr(Float, 'lat_start')[idxs]
        tctd = getattr(Float, 'UTC')[:, idxs].flatten(order='F')
        nans = np.isnan(d) | np.isnan(tctd)
        tctd = tctd[~nans]
        dctd = d[~nans]
        lonctd = np.interp(tctd, tgps, lon)
        latctd = np.interp(tctd, tgps, lat)

        plt.figure(figsize=(5, 7))
        plt.scatter(d, z, s=50, c=V*100., edgecolor='none', cmap=bwr)
        cbar = plt.colorbar(orientation='horizontal', extend='both')
        cbar.set_label(texvar+' (cm s$^{-1}$)')
        plt.clim(*clim)

        plt.xlim(np.nanmin(d), np.nanmax(d))
        plt.xlabel('Distance (km)')
        plt.ylabel('Depth (m)')
        title_str = ("Float {}").format(Float.floatID)
        plt.title(title_str)

        bathy = sandwell.interp_track(lonctd, latctd, bathy_file)
        plt.plot(dctd, bathy, 'k', linewidth=3)

        plt.ylim(np.nanmin(bathy), np.nanmax(z))

        plt.grid()


# %% Interpolated W

bwr = plt.get_cmap('bwr')
E76_hpids = np.arange(20, 40) # np.arange(31, 33)
E77_hpids = np.arange(15, 35) # np.arange(26, 28)
bathy_file = '../../data/sandwell_bathymetry/topo_17.1.img'
vars = ['Ww']#, 'U_abs', 'V_abs']
zvars = ['z']#, 'zef', 'zef']
dvars = ['dist_ctd']#, 'dist_ef', 'dist_ef']
texvars = ['$W_w$']#, '$U$', '$V$']
clims = [(-10., 10.)]#, (-100., 100.), (-100, 100.)]

var_1_vals = np.linspace(-40., 40., 80)
var_2_vals = np.linspace(-1500, 0, 500)
Xg, Zg = np.meshgrid(var_1_vals, var_2_vals)

Wgs = []
ds = []
zs = []

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    __, idxs = Float.get_profiles(hpids, ret_idxs=True)

    for var, zvar, dvar, texvar, clim in zip(vars, zvars, dvars, texvars,
                                             clims):

        V = getattr(Float, var)[:, idxs].flatten(order='F')
        z = getattr(Float, zvar)[:, idxs].flatten(order='F')
        d = getattr(Float, dvar)[:, idxs].flatten(order='F')
        zs.append(z.copy())

        tgps = getattr(Float, 'UTC_start')[idxs]
        lon = getattr(Float, 'lon_start')[idxs]
        lat = getattr(Float, 'lat_start')[idxs]
        tctd = getattr(Float, 'UTC')[:, idxs].flatten(order='F')
        nans = np.isnan(d) | np.isnan(tctd)
        tctd = tctd[~nans]
        dctd = d[~nans]
        lonctd = np.interp(tctd, tgps, lon)
        latctd = np.interp(tctd, tgps, lat)
        bathy = sandwell.interp_track(lonctd, latctd, bathy_file)

        d -= dctd[bathy.argmax()]
        ds.append(d.copy())

        nans = np.isnan(d) | np.isnan(z) | np.isnan(V)

        Wg = griddata((d[~nans], z[~nans]), V[~nans], (Xg, Zg), method='linear')
        Wgs.append(Wg.copy())

        dctd -= dctd[bathy.argmax()]
        # Spectral analysis of bathymetry.
        dx = np.mean(np.diff(dctd))
        dk = 1./dx
        ix = np.arange(-40., 40., dx)
        ibathy = np.interp(ix, dctd, bathy)
        k, Pbathy = sig.welch(ibathy, fs=dk/1000., detrend='linear')

        plt.figure()
        mWg = np.ma.masked_where(np.isnan(Wg), Wg)
        plt.pcolormesh(Xg, Zg, mWg*100., cmap=bwr)
        plt.plot(dctd, bathy, 'k', linewidth=2)
        cbar = plt.colorbar(orientation='horizontal', extend='both')
        cbar.set_label(texvar+' (cm s$^{-1}$)')
        plt.clim(*clim)
        plt.scatter(d, z, s=1, edgecolor='none', color='grey')

        plt.ylabel('Depth (m)')
        title_str = ("Float {}").format(Float.floatID)
        plt.title(title_str)
        plt.xlim(np.nanmin(d), np.nanmax(d))
        plt.ylim(np.nanmin(bathy), np.nanmax(z))
        plt.grid()

        plt.figure()
        plt.scatter(d, z, s=50, c=V*100., edgecolor='none', cmap=bwr)
        cbar = plt.colorbar(orientation='horizontal', extend='both')
        cbar.set_label(texvar+' (cm s$^{-1}$)')
        plt.clim(*clim)

        plt.xlim(np.nanmin(d), np.nanmax(d))
        plt.xlabel('Distance (km)')
        plt.ylabel('Depth (m)')
        title_str = ("Float {}").format(Float.floatID)
        plt.title(title_str)

        plt.plot(dctd, bathy, 'k', linewidth=2)

        plt.ylim(np.nanmin(bathy), np.nanmax(z))

        plt.grid()

        plt.figure(figsize=(5, 7))
        plt.loglog(k, Pbathy)



Wg_diff = Wgs[0] - Wgs[1]
mWg_diff = np.ma.masked_where(np.isnan(Wg_diff), Wg_diff)

plt.figure()
plt.pcolormesh(Xg, Zg, Wg_diff*100., cmap=bwr)
plt.plot(dctd, bathy, 'k', linewidth=2)
cbar = plt.colorbar(orientation='horizontal', extend='both')
cbar.set_label('$W_w$ difference (cm s$^{-1}$)')
plt.clim(*clim)
plt.scatter(ds[0], zs[0], s=1, edgecolor='none', color='grey')
plt.scatter(ds[0], zs[0], s=1, edgecolor='none', color='grey')

plt.ylabel('Depth (m)')
plt.xlim(np.nanmin(d), np.nanmax(d))
plt.ylim(np.nanmin(bathy), np.nanmax(z))


# %%

def wave_3(params, x):
    A, k, m, om, phi = params
    x[:, 0] = 0.
    z = cumtrapz(x[:, 3], x[:, 2], initial=0.) - A/om*np.sin(k*x[:, 0] + m*x[:, 1] - om*x[:, 2] + phi)
    return A*np.cos(k*x[:, 0] + m*z - om*x[:, 2] + phi)


def cost(params, data, func, y):
    return (func(params, data) - y).flatten()

res = []

E76_hpids = np.arange(31, 32)  # np.arange(31, 33)
E77_hpids = np.arange(26, 27)  # np.arange(26, 28)

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    __, idxs = Float.get_profiles(hpids, ret_idxs=True)

    z = Float.z[:,idxs].flatten(order='F')
    x = Float.dist_ctd[:, idxs].flatten(order='F')*1000.
    t = Float.UTC[:, idxs].flatten(order='F')*86400.
    t -= np.nanmin(t)
    W = Float.Ww[:, idxs].flatten(order='F')
    Ws = Float.Ws[:, idxs].flatten(order='F')

    nans = np.isnan(z) | np.isnan(x) | np.isnan(t) | np.isnan(W) | (z > -600)

    data = np.array([x[~nans], z[~nans], t[~nans], Ws[~nans]]).T
    W2 = W[~nans]

    x0 = [0.15, 0.004, 0.006, 0.0004, 0.]

    fit = op.leastsq(cost, x0=x0, args=(data, wave_3, W2))[0]
    print(fit)
    freq = fit[3]/(2.*np.pi)
    period = 1./freq/60.
    wavenum = fit[2]/(2.*np.pi)
    wavelen = 1./wavenum

    print("Frequency = {} s-1, Period = {} min.".format(freq, period))
    print("Wavenumber = {} m-1, Wavelength = {} m.".format(wavenum, wavelen))
    res.append(fit)

    Wm = wave_3(fit, data)
    Wm2 = wave_3(fit, np.array([x, z, t, Ws]).T)
    Wm0 = wave_3(x0, data)

    plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot(Wm*100., data[:, 1], W*100., z)#, Wm0, data[:,1])
    plt.xlabel('$W_w$ (cm s$^{-1}$)')
    plt.ylabel('Depth (m)')
    plt.subplot(2, 1, 2)
    plt.plot(data[:, 2], Wm*100., t, W*100.)#, data[:,2], Wm0)
    plt.xlabel('Time (s)')
    plt.ylabel('$W_w$ (cm s$^{-1}$)')

# %%


def wave_2(params, x):
    A, k, m, om, phi = params
    x[:, 0] = 0.
    z = cumtrapz(x[:, 3], x[:, 2], initial=0.) - A/om*np.sin(k*x[:, 0] + m*x[:, 1] - om*x[:, 2] + phi)
    return z


def wave_3(params, x):
    A, k, m, om, phi = params
    x[:, 0] = 0.
    z = wave_2(params, x)
    return A*np.cos(k*x[:, 0] + m*z - om*x[:, 2] + phi)


def cost(params, data, func, y):
    return (func(params, data) - y).flatten()

res = []

E76_hpids = np.arange(31, 32)  # np.arange(31, 33)
E77_hpids = np.arange(26, 27)  # np.arange(26, 28)

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    __, idxs = Float.get_profiles(hpids, ret_idxs=True)

    z = Float.z[:, idxs].flatten(order='F')
    x = Float.dist_ctd[:, idxs].flatten(order='F')*1000.
    t = Float.UTC[:, idxs].flatten(order='F')*86400.
    t -= np.nanmin(t)
    W = Float.Ww[:, idxs].flatten(order='F')
    Ws = Float.Ws[:, idxs].flatten(order='F')

    nans = np.isnan(z) | np.isnan(x) | np.isnan(t) | np.isnan(W) | (z > -600)

    data = np.array([x[~nans], z[~nans], t[~nans], Ws[~nans]]).T

    x0 = [0.15, 0.004, 0.006, 0.0004, 0.]

    fit = op.leastsq(cost, x0=x0, args=(data, wave_3, z[~nans]))[0]
    print(fit)
    freq = fit[3]/(2.*np.pi)
    period = 1./freq/60.
    wavenum = fit[2]/(2.*np.pi)
    wavelen = 1./wavenum

    print("Frequency = {} s-1, Period = {} min.".format(freq, period))
    print("Wavenumber = {} m-1, Wavelength = {} m.".format(wavenum, wavelen))
    res.append(fit)

    Wm = wave_3(fit, data)
    Wm2 = wave_3(fit, np.array([x, z, t, Ws]).T)
    Wm0 = wave_3(x0, data)
    zm = wave_2(fit, data)

    plt.figure()
    plt.subplot(3, 1, 1)
    plt.plot(Wm*100., data[:, 1], W*100., z)  #, Wm0, data[:,1])
    plt.xlabel('$W_w$ (cm s$^{-1}$)')
    plt.ylabel('Depth (m)')
    plt.subplot(3, 1, 2)
    plt.plot(data[:, 2], Wm*100., t, W*100.)  #, data[:,2], Wm0)
    plt.xlabel('Time (s)')
    plt.ylabel('$W_w$ (cm s$^{-1}$)')
    plt.subplot(3, 1, 3)
    plt.plot(data[:, 2], zm, t, z)


# %% Brute Force Approach

def wave_1(x, z, k, m, A=0.15, phi=0.):
    return A*np.cos(k*x + m*z + phi)

E76_hpids = np.arange(31, 33)  # np.arange(31, 33)
E77_hpids = np.arange(26, 28)  # np.arange(26, 28)

ks = np.logspace(-4, 0, 80)
ms = np.logspace(-3, 0, 60)
C = np.empty((ms.size, ks.size))
phis = np.linspace(0, 2*np.pi, 20)

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    __, idxs = Float.get_profiles(hpids, ret_idxs=True)

    z = Float.z[:,idxs].flatten(order='F')
    x = Float.dist_ctd[:, idxs].flatten(order='F')*1000.
    W = Float.Ww[:, idxs].flatten(order='F')

    nans = np.isnan(z) | np.isnan(x) | np.isnan(W) | (z > -600)

    x, z, W = x[~nans], z[~nans], W[~nans]

    for i, k in enumerate(ks):
        for j, m in enumerate(ms):
            # Loop over phases and find minimum.
            C[j, i] = np.min([np.std(wave_1(x, z, k, m, phi=phi) - W) for phi in phis])

    plt.figure()
    im = plt.pcolormesh(ks, ms, C, cmap='gray')

    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('$k$ (m$^{-1}$)')
    plt.ylabel('$m$ (m$^{-1}$)')
    plt.axhline(np.pi*2/200)
    plt.axhline(np.pi*2/600)
    plt.colorbar(im, orientation='horizontal')


# %% Is the wave stationary?

bwr = plt.get_cmap('bwr')
E76_hpids = np.arange(25, 40) # np.arange(31, 33)
E77_hpids = np.arange(20, 35) # np.arange(26, 28)
bathy_file = '../../data/sandwell_bathymetry/topo_17.1.img'

min_depth = -1400
max_depth = -200
bin_size = 40
step = 500

depth_mins = np.arange(min_depth - bin_size/2, max_depth - bin_size/2, step)
depth_maxs = np.arange(min_depth + bin_size/2, max_depth + bin_size/2, step)

fig, axs = plt.subplots(1, len(depth_mins), figsize=(16, 8), sharey=True)

for Float, hpids in zip([E76, E77], [E76_hpids, E77_hpids]):

    __, idxs = Float.get_profiles(hpids, ret_idxs=True)

    Ww = getattr(Float, 'Ww')[:, idxs].flatten(order='F')
    z = getattr(Float, 'z')[:, idxs].flatten(order='F')
    d = getattr(Float, 'dist_ctd')[:, idxs].flatten(order='F')
    t = getattr(Float, 'UTC')[:, idxs].flatten(order='F')

    # This block gets the bathymetry at the estimated position of each CTD measurement.
    # NaNs removed so array size is different to the above block.
    tgps = getattr(Float, 'UTC_start')[idxs]
    lon = getattr(Float, 'lon_start')[idxs]
    lat = getattr(Float, 'lat_start')[idxs]
    tctd = getattr(Float, 'UTC')[:, idxs].flatten(order='F')
    nans = np.isnan(d) | np.isnan(tctd)
    tctd = tctd[~nans]
    dctd = d[~nans]
    lonctd = np.interp(tctd, tgps, lon)
    latctd = np.interp(tctd, tgps, lat)
    bathy = sandwell.interp_track(lonctd, latctd, bathy_file)

    # Zero the distances at the top of the sea mount.
    d -= dctd[bathy.argmax()]

    for ax, dmin, dmax in zip(axs, depth_mins, depth_maxs):

        in_range = (z > dmin) & (z < dmax)

        C = ax.scatter(d[in_range], utils.datenum_to_datetime(t[in_range]), c=Ww[in_range], s=60, cmap=bwr, vmin=-0.08, vmax=0.08)
        ax.set_ylim(datetime.datetime(2011, 1, 2), datetime.datetime(2011, 1, 4, 12))
        ax.set_xlim(-40, 60)
        ax.set_xlabel('Distance (km)')
        ax.set_title("{} to {} m".format(dmin, dmax))

fmt = mdates.DateFormatter('%j %Hh')
axs[0].yaxis.set_major_formatter(fmt)
axs[0].set_ylabel('Time')
cbar = plt.colorbar(C, extend='both')
cbar.set_label('$W_w$ (m s$^{-1}$)')
[ax.grid() for ax in axs]


# %% Modelling float motion

# Velocity of the float.
def drdt(r, t, phi_0, U_pvals, Wf_pvals, k, l, m, om, N, f):
    x = r[0]
    y = r[1]
    z = r[2]

    Wf_g = Wf_pvals[0]
    Wf_0 = Wf_pvals[1]

    U = np.polyval(U_pvals, z)

    om2 = om**2
    f2 = f**2
    K2 = k**2 + l**2 + m**2

    dxdt = U + np.real(((k*om + 1j*l*f)/(om2 - f2))*phi_0*np.exp(1j*(k*x + l*y + m*z - om*t)))
    dydt = np.real(((l*om - 1j*k*f)/(om2 - f2))*phi_0*np.exp(1j*(k*x + l*y + m*z - om*t)))
    dzdt = (Wf_0 + np.real(((-om*K2)/((N**2 - f2)*m))*phi_0*np.exp(1j*(k*x + l*y + m*z - om*t))))/(1 - Wf_g)

    return np.array([dxdt, dydt, dzdt])

def wave_vel(r, t, phi_0, k, l, m, om, N, f):
    x = r[:, 0]
    y = r[:, 1]
    z = r[:, 2]

    om2 = om**2
    f2 = f**2
    K2 = k**2 + l**2 + m**2

    u_x = np.real(((k*om + 1j*l*f)/(om2 - f2))*phi_0*np.exp(1j*(k*x + l*y + m*z - om*t)))
    u_y = np.real(((l*om - 1j*k*f)/(om2 - f2))*phi_0*np.exp(1j*(k*x + l*y + m*z - om*t)))
    u_z = np.real(((-om*K2)/((N**2 - f2)*m))*phi_0*np.exp(1j*(k*x + l*y + m*z - om*t)))

    return (np.vstack((u_x, u_y, u_z))).T

# Model parameters.
X = 2500.
Y = 20000.
Z = 6000.

# Mean flow.
U_surf = 0.4
U_depth = 0.2
U_pvals = np.polyfit([0., -1500.], [U_surf, U_depth], 1)
f = gsw.f(-57.5)
N = 2e-3

# Float change in buoyancy with velocity.
Wf_pvals = np.polyfit([0., 0.06], [-0.14, -0.16], 1)

# Wave parameters
W_0 = 0.20
k = 2*np.pi/X
l = 2*np.pi/Y
m = 2*np.pi/Z
om = gw.omega(N, k, m, l, f)
phi_0 = W_0*(N**2 - f**2)*m/(om*(k**2 + l**2 + m**2))

args = (phi_0, U_pvals, Wf_pvals, k, l, m, om, N, f)
uargs = (phi_0, k, l, m, om, N, f)

# Integration parameters.
dt = 10.
t_0 = 0.
t_1 = 14000.
t = np.arange(t_0, t_1, dt)

# Initial conditions.
x_0 = 0.
y_0 = 0.
z_0 = 0.
r_0 = np.array([x_0, y_0, z_0])

# This integrator calls FORTRAN odepack to solve the problem.
r = odeint(drdt, r_0, t, args)
u = wave_vel(r, t, *uargs)

fig, axs = plt.subplots(1, 5, sharey=True, figsize=(14, 6))
axs[0].set_ylabel('$z$')
axs[0].plot(u[:, 0], r[:, 2])
axs[0].set_xlabel('$U$ (wave)')
axs[1].plot(u[:, 1], r[:, 2])
axs[1].set_xlabel('$V$ (wave)')
axs[2].plot(u[:, 2], r[:, 2])
axs[2].set_xlabel('$W$ (wave)')
axs[3].plot(u[:, 0] + np.polyval(U_pvals, r[:, 2]), r[:, 2])
axs[3].set_xlabel('$U$ (wave + mean)')
axs[4].plot(r[:, 0], r[:, 2])
axs[4].set_xlabel('$x$')

pfl = E77.get_profiles(26)
fig, axs = plt.subplots(1, 4, sharey=True, figsize=(12, 6))
axs[0].set_ylabel('$z$')
axs[0].plot(pfl.U_abs, pfl.zef)
axs[0].set_xlabel('$U$')
axs[1].plot(pfl.V_abs, pfl.zef)
axs[1].set_xlabel('$V$')
axs[2].plot(pfl.Ww, pfl.z)
axs[2].set_xlabel('$W$')
axs[3].plot(pfl.dist_ctd - np.nanmin(pfl.dist_ctd), pfl.z)
axs[3].set_xlabel('$x$')
