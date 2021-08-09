#define _USE_MATH_DEFINES
#include <math.h>
#include "cfuncs.h"

/*
 * This code is based on Dave Boore's fortran function icmpmx, which in turn
 * was based on ucmpmx, written by Bob Youngs and I. Idriss). It was re-
 * written in python/cython by Heather Schovanec (8/2018) and rewritten in
 * C by Bruce Worden (8/2018).
 * Note that this code does no resampling. It is assumed that the data
 * provided to this function has been sufficiently resampled. See, for
 * example, Boore and Goulet (2014), Bull Earthquake Eng, 12:203-216,
 * DOI 10.1007/s10518-013-9574-9.
 */
void calculate_spectrals_c(double *acc, int np, double dt, double period,
                           double damping, double *sacc, double *svel,
                           double *sdis)
{
    double w = 2 * M_PI / period;
    double d = damping;
    double wd = sqrt(1. - d * d) * w;
    double e = exp(-1 * d * w * dt);
    double sine = e * sin(wd * dt);
    double cosine = e * cos(wd * dt);

    double w2 = w * w;
    double w3 = w2 * w;
    double w2i = 1.0 / w2;
    double wdi = 1.0 / wd;
    double dw = d * w;
    double ddtw3 = 2. * d / (dt * w3);

    // Values that will change with each iteration
    double a;
    double b;
    double dug;
    double g;
    double gw2i;
    double dugw2i;
    double dugw2idt;
    int k;

    g = acc[0];
    dug = acc[1] - g;
    gw2i = g * w2i;
    dugw2i = dug * w2i;
    dugw2idt = dugw2i / dt;
    b = 0 + gw2i - ddtw3 * dug;
    a = wdi * 0 + dw * wdi * b + wdi * dugw2idt;
    sdis[0] = a * sine + b * cosine + ddtw3 * dug - gw2i - dugw2i;
    svel[0] = a * (wd * cosine - dw * sine) -
              b * (wd * sine + dw * cosine) -
              dugw2idt;
    sacc[0] = -2. * dw * svel[0] - w2 * sdis[0];
    for (k = 1; k < np - 1; k++)
    {
        g = acc[k];
        dug = acc[k + 1] - g;
        gw2i = g * w2i;
        dugw2i = dug * w2i;
        dugw2idt = dugw2i / dt;
        b = sdis[k - 1] + gw2i - ddtw3 * dug;
        a = wdi * svel[k - 1] + dw * wdi * b + wdi * dugw2idt;
        sdis[k] = a * sine + b * cosine + ddtw3 * dug -
                  gw2i - dugw2i;
        svel[k] = a * (wd * cosine - dw * sine) -
                  b * (wd * sine + dw * cosine) -
                  dugw2idt;
        sacc[k] = -2. * dw * svel[k] - w2 * sdis[k];
    }
    return;
}
