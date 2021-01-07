# Computing waveform metrics

Waveform metrics are defined by selecting an intensity measure type (IMT)
and an intensity measure component (IMC). IMTs typically describe the
parameter that is used to represent some aspect of the ground motion, such
as PGA or duration. IMCs describe how the different components are
handled. 

A table of combinations of IMT and IMCs indicating which combinations
we currently support is printed by the `list_metrics` program:

```

    Table of supported IMC/IMT combinations is below.

    Notes:

    The "channels" IMC will result in three IMC channels
    called "H1", "H2", and "Z".

    The "gmrotd" and "rotd" IMCs will need to be specified as "gmrotd50"
    for the Geometric Mean 50th percentile, rotd100 for the 100th percentile,
    and so forth.

                           fas arias duration pga pgv sa
imc
arithmetic_mean              Y     Y        Y   Y   Y  Y
gmrotd                       N     N        Y   Y   Y  Y
quadratic_mean               Y     N        Y   Y   Y  Y
rotd                         N     N        Y   Y   Y  Y
geometric_mean               Y     N        Y   Y   Y  Y
channels                     N     N        Y   Y   Y  Y
radial_transverse            N     N        Y   Y   Y  Y
greater_of_two_horizontals   N     N        Y   Y   Y  Y

```
