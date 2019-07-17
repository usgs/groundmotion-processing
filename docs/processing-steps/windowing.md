# Windowing Data

It is fundamental to our algorithms that we seprate a pre-event noise window
from the signal. This section controls options regarding this.

First, we try to estimate the time of the earliest arriving seismic energy
(the p-wave). We call this the "split" time because it should be the boundary
between the signal and pre-event noise. Since the config options for how to do
this are relatively complicated, we have a separate section dedicated to it
below called "pickers".

However, we also have options for how long to trim the singnal window. This is
meant to be a more accurate representation of the signal duration than what one
would want to use for the "time_after" option in the "fetchers" section. The
options for setting "signal_end" are:

* `method: model` -- This uses a model of shaking duration. The current default
  is the Afshari and Stewart (2016) model. The abbreviation "AS16" is mapped
  to the OpenQuake library via the `modules.yml` file, located in the
  `gmprocess/data` directory. Additionally, the `epsilon` is the number of
  standard deviations to move the end of the signal window out beyond the mean
  shaking duration predicted by the model.

* `method: velocity` -- This is a more crude method that uses an assumed wave
  velocty (`vmin`) to estimate the end of the signal window. When this option
  is set, it also uses the `floor` option to avoid very short durations at
  short source-to-site distances.

