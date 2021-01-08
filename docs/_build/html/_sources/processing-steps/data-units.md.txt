# Data Units

The units of the various quantities can change throughout the steps of data processing.
Those units are detailed here.

## Input from Time Series

Time series data input into ground motion processing could come as one of
several physical quantities (accleration, velocity, displacement) in any number
of different units (m/s^2, cm/s^2, cm/s, m, etc.). Centimeters per second
squared (or gals) seems to be a fairly standard unit for acceleration, and
centimeters per second fairly standard for velocity, though this is by no means
guaranteed and dictated by the authors of the original data.

Raw data from sensors is in counts, and usually the metadata for the time
series contains factors to convert these values into physical units.

## Output from File Readers

Acceleration data from file readers is always in gals, and velocity is always
in cm/s. Displacement and other quantities of time-series data are not
currently supported. Data that is provided in counts is kept in counts, and can
be converted to physical units by use of the "remove_response" processing step.

## Output from Stream Metrics Calculations

The units of intensity measure types (IMTs) output by stream metrics
calculations is below:

| IMT                        | Units       |
| -------------------------- | ----------- |
| Peak Ground Acceleration   | %g          |
| Peak Ground Velocity       | cm/s        |
| Spectral Acceleration      | %g          |
| Arias Intensity            | m/s         |
| Fourier Amplitude Spectrum | cm/s        |
| Duration                   | s           |

## Distance and Depth

Epicentral and hypocentral distances are always in kilometers, as are
earthquake depths. Station elevations should always be in meters.

