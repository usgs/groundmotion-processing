#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is for computation of theoretical amplitude spectrum methods.
"""

import numpy as np
from scipy.optimize import minimize
from obspy.geodetics.base import gps2dist_azimuth
from gmprocess.waveform_processing.processing_step import ProcessingStep

OUTPUT_UNITS = ["ACC", "VEL", "DISP"]
M_TO_KM = 1.0 / 1000


@ProcessingStep
def fit_spectra(
    st,
    origin,
    kappa=0.035,
    RP=0.55,
    VHC=0.7071068,
    FSE=2.0,
    density=2.8,
    shear_vel=3.7,
    R0=1.0,
    moment_factor=100,
    min_stress=0.1,
    max_stress=10000,
    config=None,
):
    """
    Fit spectra vaying stress_drop and moment.

    Args:
        st (StationStream):
            Stream of data.
        origin (ScalarEvent):
             ScalarEvent object.
        kappa (float):
            Site diminution factor (sec). Typical value for active cruststal
            regions is about 0.03-0.04, and stable continental regions is about
            0.006.
        RP (float):
            Partition of shear-wave energy into horizontal components.
        VHC (float):
            Partition of shear-wave energy into horizontal components
            1 / np.sqrt(2.0).
        FSE (float):
            Free surface effect.
        density (float):
            Density at source (gm/cc).
        shear_vel (float):
            Shear-wave velocity at source (km/s).
        R0 (float):
            Reference distance (km).
        moment_factor (float):
            Multiplicative factor for setting bounds on moment, where the
            moment (from the catalog moment magnitude) is multiplied and
            divided by `moment_factor` to set the bounds for the spectral
            optimization.
        min_stress (float):
            Min stress for fit search (bars).
        max_stress (float):
            Max stress for fit search (bars).
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream with fitted spectra parameters.
    """
    for tr in st:
        # Only do this for horizontal channels for which the smoothed spectra
        # has been computed.
        if tr.hasCached("smooth_signal_spectrum") and tr.hasParameter(
            "corner_frequencies"
        ):
            event_mag = origin.magnitude
            event_lon = origin.longitude
            event_lat = origin.latitude
            dist = (
                gps2dist_azimuth(
                    lat1=event_lat,
                    lon1=event_lon,
                    lat2=tr.stats["coordinates"]["latitude"],
                    lon2=tr.stats["coordinates"]["longitude"],
                )[0]
                * M_TO_KM
            )

            # Use the smoothed spectra for fitting
            smooth_signal_dict = tr.getCached("smooth_signal_spectrum")
            freq = np.array(smooth_signal_dict["freq"])
            obs_spec = np.array(smooth_signal_dict["spec"])

            # -----------------------------------------------------------------
            # INITIAL VALUES
            # Need an approximate stress drop as initial guess
            stress_0 = np.sqrt(min_stress * max_stress)
            moment_0 = moment_from_magnitude(event_mag)

            # Array of initial values
            x0 = (np.log(moment_0), np.log(stress_0))

            # Bounds
            stress_bounds = (np.log(min_stress), np.log(max_stress))

            # multiplicative factor for moment bounds
            moment_bounds = (
                x0[0] - np.log(moment_factor),
                x0[0] + np.log(moment_factor),
            )

            bounds = (moment_bounds, stress_bounds)

            # Frequency limits for cost function
            freq_dict = tr.getParameter("corner_frequencies")
            fmin = freq_dict["highpass"]
            fmax = freq_dict["lowpass"]

            # -----------------------------------------------------------------
            # CONSTANT ARGUMENTS

            cargs = (
                freq,
                obs_spec,
                fmin,
                fmax,
                dist,
                kappa,
                RP,
                VHC,
                FSE,
                shear_vel,
                density,
                R0,
            )

            result = minimize(
                spectrum_cost,
                x0,
                args=cargs,
                method="L-BFGS-B",
                jac=False,
                bounds=bounds,
                tol=1e-4,
                options={"disp": False},
            )

            moment_fit = np.exp(result.x[0])
            magnitude_fit = magnitude_from_moment(moment_fit)
            stress_drop_fit = np.exp(result.x[1])
            f0_fit = brune_f0(moment_fit, stress_drop_fit)

            # Hessian (H) is in terms of normalized moment and stress drop
            # Covariance matrix is sigma^2 * H^-1.
            inv_hess = result.hess_inv.todense()

            # Estimate of sigma^2 is sum of squared residuals / (n - p)
            # NOTE: we are NOT accounting for the correlation across
            # frequencies and so we are underestimating the variance.
            SSR = result.fun
            sigma2 = SSR / (len(freq) - len(result.x))
            COV = sigma2 * inv_hess
            sd = np.sqrt(np.diagonal(COV))

            # mag_lower = magnitude_from_moment(np.exp(result.x[0]-sd[0]))
            # mag_upper = magnitude_from_moment(np.exp(result.x[0]+sd[0]))
            # stress_drop_lower = np.exp(result.x[1]-sd[1])
            # stress_drop_upper = np.exp(result.x[1]+sd[1])

            # Get the fitted spectrum and then calculate the goodness-of-fit
            # metrics
            fit_spec = model((moment_fit, stress_drop_fit), freq, dist, kappa)
            mean_squared_error = np.mean((obs_spec - fit_spec) ** 2)

            # R^2 (Coefficient of Determination) is defined as 1 minus the
            # residual sum of squares (SSR) divided by the total sum of squares
            # (SST)
            ssr = np.sum((obs_spec - fit_spec) ** 2)
            sst = np.sum((obs_spec - np.mean(obs_spec)) ** 2)
            r_squared = 1 - (ssr / sst)

            fit_spectra_dict = {
                "stress_drop": stress_drop_fit,
                "stress_drop_lnsd": sd[1],
                "epi_dist": dist,
                "kappa": kappa,
                "moment": moment_fit,
                "moment_lnsd": sd[0],
                "magnitude": magnitude_fit,
                "f0": f0_fit,
                "minimize_message": result.message,
                "minimize_success": result.success,
                "mean_squared_error": mean_squared_error,
                "R2": r_squared,
            }
            tr.setParameter("fit_spectra", fit_spectra_dict)

    return st


def spectrum_cost(
    x,
    freq,
    obs_spec,
    fmin,
    fmax,
    dist,
    kappa,
    RP,
    VHC=0.7071068,
    FSE=2.0,
    shear_vel=3.7,
    density=2.8,
    R0=1.0,
    gs_mod="REA99",
    q_mod="REA99",
    crust_mod="BT15",
):
    """
    Function to compute RMS log residuals for optimization.

    Args:
        x (tuple):
            Tuple of the moment (dyne-cm) and the stress drop (bars).
        freq (array):
            Numpy array of frequencies (Hz).
        obs_spec (array):
            Numpy array of observed Fourier spectral amplitudes.
        fmin (float):
            Minimum frequency to use in computing residuals.
        fmax (float):
            Maximum frequency to use in computing residuals.
        dist (float):
            Distance (km).
        kappa (float): Site diminution factor (sec). Typical value for active cruststal
            regions is about 0.03-0.04, and stable continental regions is about 0.006.
        RP (float):
            Partition of shear-wave energy into horizontal components.
        VHC (float):
            Partition of shear-wave energy into horizontal components
            1 / np.sqrt(2.0).
        FSE (float):
            Free surface effect.
        shear_vel (float):
            Shear-wave velocity at source (km/s).
        density (float):
            Density at source (gm/cc).
        R0 (float):
            Reference distance (km).
        gs_model (str):
            Name of model for geometric attenuation. Currently only supported value:
            - 'REA99' for Raoof et al. (1999)
        q_model (str):
            Name of model for anelastic attenuation. Currently only supported value:
            - 'REA99' for Raoof et al. (1999)
            - 'none' for no anelastic attenuation
        crust_mod (str):
            Name of model for crustal amplification. Currently onlysupported value:
            - 'BT15' for Boore and Thompson (2015)
            - 'none' for no crustal amplification model.

    Returns:
        float: Sum of squared logarithmic residuals.

    """
    # Exponentiate the paramters
    xexp = []
    for xx in x:
        xexp.append(np.exp(xx))

    mod_spec = model(
        xexp,
        freq,
        dist,
        kappa,
        RP,
        VHC,
        FSE,
        shear_vel,
        density,
        R0,
        gs_mod,
        q_mod,
        crust_mod,
    )

    # Remove non-positive values of obs_spec and apply corner frequency
    # constraints
    keep = (obs_spec > 0) & (freq >= fmin) & (freq <= fmax)

    log_residuals = np.log(obs_spec[keep]) - np.log(mod_spec[keep])
    return np.sum(log_residuals**2)


def model(
    x,
    freq,
    dist,
    kappa,
    RP=0.55,
    VHC=0.7071068,
    FSE=2.0,
    shear_vel=3.7,
    density=2.8,
    R0=1.0,
    gs_mod="REA99",
    q_mod="REA99",
    crust_mod="BT15",
):
    """
    Piece together a model of the ground motion spectrum.

    Args:
        x (tuple):
            Tuple of the natural log of moment (dyne-cm) and the natural log of stress
            drop (bars).
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        dist (float):
            Distance (km).
        kappa (float):
            Site diminution factor (sec). Typical value for active cruststal
            regions is about 0.03-0.04, and stable continental regions is about 0.006.
        RP (float):
            Partition of shear-wave energy into horizontal components.
        VHC (float):
            Partition of shear-wave energy into horizontal components 1 / np.sqrt(2.0).
        FSE (float):
            Free surface effect.
        shear_vel (float):
            Shear-wave velocity at source (km/s).
        density (float):
            Density at source (gm/cc).
        R0 (float):
            Reference distance (km).
        gs_model (str):
            Name of model for geometric attenuation. Currently only supported value:
            - 'REA99' for Raoof et al. (1999)
        q_model (str):
            Name of model for anelastic attenuation. Currently only supported value:
            - 'REA99' for Raoof et al. (1999)
            - 'none' for no anelastic attenuation
        crust_mod (str):
            Name of model for crustal amplification. Currently only supported value:
            - 'BT15' for Boore and Thompson (2015)
            - 'none' for no crustal amplification model.

    Returns:
        Array of spectra model.
    """
    source_mod = brune(
        freq,
        x[0],
        x[1],
        RP=RP,
        VHC=VHC,
        FSE=FSE,
        shear_vel=shear_vel,
        density=density,
        R0=R0,
    )
    path_mod = path(freq, dist, gs_mod, q_mod)
    site_mod = site(freq, kappa, crust_mod)
    return source_mod * path_mod * site_mod


def brune(
    freq,
    moment,
    stress_drop=150,
    RP=0.55,
    VHC=0.7071068,
    FSE=2.0,
    shear_vel=3.7,
    density=2.8,
    R0=1.0,
    output_units="ACC",
):
    """
    Compute Brune (1970, 1971) earthquake source spectrum.


    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        moment (float):
            Earthquake moment (dyne-cm).
        stress_drop (float):
            Earthquake stress drop (bars).
        RP (float):
            Partition of shear-wave energy into horizontal components.
        VHC (float):
            Partition of shear-wave energy into horizontal components
            1 / np.sqrt(2.0).
        FSE (float):
            Free surface effect.
        shear_vel (float):
            Shear-wave velocity at source (km/s).
        density (float):
            Density at source (gm/cc).
        R0 (float):
            Reference distance (km).
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

    f0 = brune_f0(moment, stress_drop, shear_vel)
    S = 1 / (1 + (freq / f0) ** 2)
    C = RP * VHC * FSE / (4 * np.pi * density * shear_vel**3 * R0) * 1e-20

    if output_units == "ACC":
        fpow = 2.0
    elif output_units == "VEL":
        fpow = 1.0
    elif output_units == "DISP":
        fpow = 0.0

    displacement = C * moment * S

    return (2 * np.pi * freq) ** fpow * displacement


def brune_f0(moment, stress_drop, shear_vel=3.7):
    """
    Compute Brune's corner frequency.

    Args:
        moment (float):
            Earthquake moment (dyne-cm).
        stress_drop (float):
            Earthquake stress drop (bars).
        shear_vel (float):
            Shear-wave velocity at source (km/s).

    Returns:
        float: Brune corner frequency (Hz).
    """
    f0 = 4.906e6 * shear_vel * (stress_drop / moment) ** (1.0 / 3.0)
    return f0


def brune_stress(moment, f0, shear_vel=3.7):
    """
    Compute Brune's stress drop.

    Args:
        moment (float):
            Earthquake moment (dyne-cm).
        f0 (float):
            Brune corner frequency (Hz).
        shear_vel (float):
            Shear-wave velocity at source (km/s).

    Returns:
        float: Brune stress drop (bars).
    """
    stress_drop = ((f0 / (4.906e6 * shear_vel)) ** 3) * moment
    return stress_drop


def moment_from_magnitude(magnitude):
    """
    Compute moment from moment magnitude.

    Args:
        magnitude (float):
            Moment magnitude.

    Returns:
        float: Seismic moment (dyne-cm).
    """
    return 10 ** (1.5 * magnitude + 16.05)


def magnitude_from_moment(moment):
    """
    Compute moment from moment magnitude.

    Args:
        moment (float):
            Seismic moment (dyne-cm).

    Returns:
        float: Moment magnitude.
    """
    return 2.0 / 3.0 * (np.log10(moment) - 16.05)


def path(freq, dist, gs_mod="REA99", q_mod="REA99"):
    """
    Path term, including geometric and anelastic attenuation.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        dist (float):
            Distance (km).
        gs_model (str):
            Name of model for geometric attenuation. Currently only supported value:
            - 'REA99' for Raoof et al. (1999)
        q_model (str):
            Name of model for anelastic attenuation. Currently only supported value:
            - 'REA99' for Raoof et al. (1999)
            - 'none' for no anelastic attenuation

    Returns:
        Array of path effects.
    """
    geom_spread = geometrical_spreading(freq, dist, model=gs_mod)
    ae_att = anelastic_attenuation(freq, dist, model=q_mod)

    return geom_spread * ae_att


def site(freq, kappa, crust_mod="BT15"):
    """
    Site term, including crustal amplification and kappa.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        kappa (float):
            Site diminution factor (sec). Typical value for active cruststal
            regions is about 0.03-0.04, and stable continental regions is about 0.006.
        crust_mod (str):
            Name of model for crustal amplification. Currently only supported value:
            - 'BT15' for Boore and Thompson (2015)
            - 'none' for no crustal amplification model.
    """
    crust_amp = crustal_amplification(freq, model=crust_mod)
    dim = np.exp(-np.pi * kappa * freq)
    return crust_amp * dim


def crustal_amplification(freq, model="BT15"):
    """
    Crustal amplification model.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        model (str):
            Name of model for crustal amplification. Currently only supported value:
            - 'BT15' for Boore and Thompson (2015)
            - 'none' for no crustal amplification model.
    """
    if model == "BT15":
        freq_tab = np.array(
            [
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
                60.3,
            ]
        )
        amplification_tab = np.array(
            [1.00, 1.01, 1.03, 1.06, 1.10, 1.19, 1.39, 1.58, 1.77, 2.24, 2.75, 4.49]
        )

        # Interpolation should be linear freq, log amplification
        log_amp_tab = np.log(amplification_tab)
        log_amp_interp = np.interp(freq, freq_tab, log_amp_tab)
        crustal_amps = np.exp(log_amp_interp)
    elif model == "none":
        crustal_amps = np.ones_like(freq)
    else:
        raise ValueError("Unsupported crustal amplification model.")

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
            Name of model for geometric attenuation. Currently only supported value:
            - 'REA99' for Raoof et al. (1999)

    Returns:
        geom (float): anelastic attenuation factor.
    """

    if model == "REA99":
        dist_cross = 40.0
        if dist <= dist_cross:
            geom = dist ** (-1.0)
        else:
            geom = (dist * dist_cross) ** (-0.5)
    else:
        raise ValueError("Unsupported anelastic attenuation model.")
    return geom


def anelastic_attenuation(freq, dist, model="REA99"):
    """
    Effect of anelastic attenuation.

    Args:
        freq (array):
            Numpy array of frequencies for computing spectra (Hz).
        dist (float):
            Distance (km).
        model (str):
            Name of model for anelastic attenuation. Currently only supported value:
            - 'REA99' for Raoof et al. (1999)
            - 'none' for no anelastic attenuation

    Returns:
        Array of aneastic attenuation factor.
    """

    if model == "REA99":
        # Frequency dependent quality factor
        quality_factor = 180 * freq**0.45
        cq = 3.5
        anelastic = np.exp(-np.pi * freq * dist / quality_factor / cq)
    elif model == "none":
        anelastic = np.ones_like(freq)
    else:
        raise ValueError("Unsupported anelastic attenuation model.")

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
        float: Adjusted distance.
    """

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
        logH = c0 + c1 * (magnitude - Mt) + c2 * (magnitude - Mt) ** 2
        h = 10 ** (logH)
    else:
        raise ValueError("Unsupported finite fault adjustment model.")

    return h
