"""
This module is for computation of theoretical amplitude spectrum methods.
"""

import numpy as np

OUTPUT_UNITS = ["ACC", "VEL", "DISP"]

# -----------------------------------------------------------------------------
# Some constantts; probably should put these in a config file at some point:

# Radiation pattern factor (Boore and Boatwright, 1984))
RP = 0.55

# Partition of shear-wave energy into horizontal components
VHC = 1/np.sqrt(2)

# Free surface effect
FSE = 2.0

# Density at source (gm/cc)
DENSITY = 2.8

# Shear-wave velocity at source (km/s)
SHEAR_VEL = 3.7

# Reference distance (km)
R0 = 1.0


def model(freq, dist, kappa,
          magnitude, stress_drop=150,
          gs_mod="REA99", q_mod="REA99",
          crust_mod="BT15"):
    """
    Piece together a model of the ground motion spectrum.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        dist (float):
            Distance (km).
        kappa (float):
            Site diminution factor (sec). Typical value for active cruststal
            regions is about 0.03-0.04, and stable continental regions is about
            0.006.
        magnitude (float):
            Earthquake moment magnitude.
        stress_drop (float):
            Earthquake stress drop (bars).
        gs_model (str):
            Name of model for geometric attenuation. Currently only supported
            value:
                - 'REA99' for Raoof et al. (1999)
        q_model (str):
            Name of model for anelastic attenuation. Currently only supported
            value:
                - 'REA99' for Raoof et al. (1999)
        crust_mod (str):
            Name of model for crustal amplification. Currently only supported
            value:
                - 'BT15' for Boore and Thompson (2015)

    Returns:
        Array of spectra model.
    """
    source_mod = brune(freq, magnitude, stress_drop)
    path_mod = path(freq, dist, gs_mod, q_mod)
    site_mod = site(freq, kappa, crust_mod)
    return source_mod * path_mod * site_mod


def brune(freq, magnitude, stress_drop=150, output_units="ACC"):
    """
    Compute Brune (1970, 1971) earthquake source spectrum.


    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        magnitude (float):
            Earthquake moment magnitude.
        stress_drop (float):
            Earthquake stress drop (bars).
        output_units (str):
            Time domain equivalent units for the output spectrum. One of:
                - "ACC" for acceleration, giving Fourier spectra units of cm/s.
                - "VEL" for velocity, giving Fourier spectra units of cm.
                - "DISP"

    Returns:
        Array of source spectra.
    """
    if output_units not in OUTPUT_UNITS:
        raise ValueError("Unsupported value for output_units.")

    M0 = 10**(1.5 * magnitude + 16.05)
    f0 = 4.9e6 * SHEAR_VEL * (stress_drop/M0)**(1/3)
    S = 1/(1 + (freq/f0)**2)
    C = RP * VHC * FSE/(4 * np.pi * DENSITY * SHEAR_VEL**3 * R0) * 1e-20

    if output_units == "ACC":
        fpow = 2.0
    elif output_units == "VEL":
        fpow = 1.0
    elif output_units == "DISP":
        fpow = 0.0

    displacement = C * M0 * S

    return (2 * np.pi * freq)**fpow * displacement


def path(freq, dist, gs_mod="REA99", q_mod="REA99"):
    """
    Path term, including geometric and anelastic attenuation.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        dist (float):
            Distance (km).
        gs_model (str):
            Name of model for geometric attenuation. Currently only supported
            value:
                - 'REA99' for Raoof et al. (1999)
        q_model (str):
            Name of model for anelastic attenuation. Currently only supported
            value:
                - 'REA99' for Raoof et al. (1999)

    Returns:
        Array of path effects.
    """
    geom_spread = geometrical_spreading(freq, dist, model='REA99')
    ae_att = anelastic_attenuation(freq, dist, model='REA99')

    return geom_spread * ae_att


def site(freq, kappa, crust_mod='BT15'):
    """
    Site term, including crustal amplificaiton and kappa.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        kappa (float):
            Site diminution factor (sec). Typical value for active cruststal
            regions is about 0.03-0.04, and stable continental regions is about
            0.006.
        crust_mod (str):
            Name of model for crustal amplification. Currently only supported
            value:
                - 'BT15' for Boore and Thompson (2015)
    """
    crust_amp = crustal_amplification(freq, model="BT15")
    dim = np.exp(-np.pi * kappa * freq)
    return crust_amp * dim


def crustal_amplification(freq, model="BT15"):
    """
    Crustal amplificaiton model.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        model (str):
            Name of model for crustal amplification. Currently only supported
            value:
                - 'BT15' for Boore and Thompson (2015)
    """
    if model != 'BT15':
        raise ValueError('Unsupported crustal amplificaiton model.')

    if model == 'BT15':
        freq_tab = np.array([
            0.001,
            0.009,
            0.025,
            0.049,
            0.081,
            0.15,
            0.37,
            0.68,
            1.11,
            2.36,
            5.25,
            60.3
        ])
        amplificaiton_tab = np.array([
            1.00,
            1.01,
            1.03,
            1.06,
            1.10,
            1.19,
            1.39,
            1.58,
            1.77,
            2.24,
            2.75,
            4.49
        ])

        # Interpolation should be linear freq, log amplification
        log_amp_tab = np.log(amplificaiton_tab)
        log_amp_interp = np.interp(freq, freq_tab, log_amp_tab)
        crustal_amps = np.exp(log_amp_interp)

    return crustal_amps


def geometrical_spreading(freq, dist, model="REA99"):
    """
    Effect of geometrical spreading.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        dist (float):
            Distance (km).
        model (str):
            Name of model for geometric attenuation. Currently only supported
            value:
                - 'REA99' for Raoof et al. (1999)

    Returns:
        Array of anelastic attenuation factor.
    """
    if model != 'REA99':
        raise ValueError('Unsupported anelastic attenuation model.')

    if model == 'REA99':
        dist_cross = 40.0
        if dist <= dist_cross:
            geom = dist**(-1.0)
        else:
            geom = (dist/dist_cross)**(-0.5)
    return geom


def anelastic_attenuation(freq, dist, model='REA99'):
    """
    Effect of anelastic attenuation.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        dist (float):
            Distance (km).
        model (str):
            Name of model for anelastic attenuation. Currently only supported
            value:
                - 'REA99' for Raoof et al. (1999)

    Returns:
        Array of aneastic attenuation factor.
    """

    if model != 'REA99':
        raise ValueError('Unsupported anelastic attenuation model.')

    if model == 'REA99':
        # Frequency dependent quality factor
        quality_factor = 180*freq**0.45
        cq = 3.5
        anelastic = np.exp(-np.pi*freq*dist/quality_factor/cq)

    return anelastic


def finite_fault_factor(magnitude, model="BT15"):
    """
    Finite fault factor for converting Rrup to an equivalent point source
    distance.

    Args:
        magnitude (float):
            Earthquake moment magnitude.
        model (str):
            Which model to use; currently only suppport "BT15".

    Returns:
        Adjusted distance.
    """

    if model != "BT15":
        raise ValueError("Unsupported finite fault adjustment model.")

    if model == "BT15":
        Mt1 = 5.744
        Mt2 = 7.744
        if magnitude < Mt1:
            c0 = 0.7497
            c1 = 0.4300
            c2 = 0.0
            Mt = Mt1
        elif magnitude < Mt2:
            c0 = 0.7497
            c1 = 0.4300
            c2 = -0.04875
            Mt = Mt1
        else:
            c0 = 1.4147
            c1 = 0.2350
            c2 = 0
            Mt = Mt2
        logH = c0 + c1 * (magnitude - Mt) + c2*(magnitude - Mt)**2
        h = 10**(logH)

    return h
