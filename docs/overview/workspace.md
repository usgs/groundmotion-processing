# Workspace

The workspace serves as a container to hold the inputs, important
intermediate results, and outputs. It also includes provenance
information describing the processing steps performed on the data.

We use the [ASDF](https://academic.oup.com/gji/article/207/2/1003/2583765)
HDF-5 layout, which includes specifications for earthquake information,
station metadata, and waveform time histories. We include information
not explicitly covered in the ASDF format specification in the
`AuxiliaryData` group.

## Extension of ASDF HDF-5 Layout

We add several additional groups to the `AuxiliaryData` section:

* `WaveformMetrics` for ground-motion intensity metrics, such as peak
values, response spectra, and Fourier amplitude spectra.

* `StationMetrics` for event station information, such as epicentral
distance and rupture distance.

* (Potential future addition) `SurfaceWaveforms` for waveform time histories
  on a surface.

* (Potential future addition) `RuptureModels` for finite-fault earthquake
  rupture models.


<figure>
  <img width="600px" src="figs/asdf_layout.png" alt="ASDF layout"/>
  <figcaption>Diagram of group and dataset hierarchy in extension of the
ASDF HDF-5 layout</figcaption>
</figure>


### Waveform Metrics

Waveform metrics are quantities derived from the waveform time
histories, such as peak values (maximum absolute values), duration,
response spectra, and Fourier amplitude spectra. Although in some
cases they may be associated with a single channel (for example,
maximum absolute value) they are often a scalar value associated with
multiple channels (for example, RotD50 from the channels with the
horizontal components).

#### Waveform Metrics Hierarchy

Following the ASDF layout for waveforms and station metadata, the
hierarchy is

`WaveformMetrics` (group) -> *NET.STA* (group)
-> *NET.STA.LOC__START__END__WTAG__TAG* (dataset)

  * **NET**: FDSN network code (or equivalent)
  * **STA**: Station code
  * **LOC**: Location code
  * **START__END**: Channel start and end timestamps from `Waveforms`.
  * **WTAG**: Tag associated with waveform processing
  * **TAG**: Tag associated with process to compute metrics

We do not include the channel code, because many metrics involve
multiple channels (horizontal components). The components are included
in the metrics as attributes as necessary.

The dataset is a string corresponding to XML, similar to the `QuakeML`
and `StationXML` datasets.

The XML hierarchy follows the ShakeMap convention of intensity metric
followed by intensity metric type (`waveform_metrics` -> *IM* -> *IMT*).

  * **IM**: Intensity metric (peak ground acceleration, peak ground
velocity, response spectra, Fourier amplitude spectra)
  * **IMT**: Intensity metric type (maximum component, geometric mean,
RotD50, etc)

Sample XML for a waveform metrics dataset:
```xml
<waveform_metrics>
    <pga>
        <rot_d50 units="m/s**2">0.45</rot_d50>
        <maximum_component units="m/s**2">0.23</maximum_component>
        <component name="east" units="m/s**2">0.23</component>
        <component name="up" units="m/s**2">0.11</component>
    </pga>
    <sa percent_damping="5.0">
        <rot_d50 units="g">
	        <value period="3.0">0.2</value>
	        <value period="1.0">0.6</value>
	        <value period="0.3">0.3</value>
        </rot_d50>
    </sa>
    <pgv>
        <maximum_component units="m/s">0.012</maximum_component>
        <component name="east" units="m/s">0.012</component>
        <component name="up" units="m/s">0.008</component>
    </pgv>
</waveform_metrics>
```

### Station Metrics

Station metrics are quantities that depend on the earthquake rupture
and station, such as epicentral distance, hypocentral distance,
Joyner-Boore distance, and closest distance to the rupture surface.

#### Station Metrics Hierarchy

Following the ASDF layout for waveforms and station metadata, the
hierarchy is

`StationMetrics` (group) -> *NET.STA* (group)
-> *NET.STA__EVENTID__TAG* (dataset)

  * **NET**: FDSN network code (or equivalent)
  * **STA**: Station code
  * **EVENTID**: ComCat event id (or equivalent)
  * **TAG**: Tag associated with processing to compute metrics

The dataset is a string corresponding to XML, similar to the `QuakeML`
and `StationXML` datasets.

Sample XML for a station metrics dataset:
```xml
<station_metrics>
  <hypocentral_distance units="km">10.2</hypocentral_distance>
  <epicentral_distance units="km">2.3</epicentral_distance>
</station_metrics>
```

### Surface Waveforms (potential future addition)

**Use case**: Output from ground-motion simulations.

**Status**: Under discussion.

Output from seismic wave propagation simulations often include the
waveform time histories on the ground surface or vertical slices. This
auxiliary data group would provide a standard layout for specifying
the topology of the surface and the time histories on that surface.

### Rupture Models (potential future addition)

**Use case**: Finite-source rupture models from inversions of real
earthquakes and scenario (hypothetical) earthquakes.

**Status**: Under discussion.

In order to compute station metrics associated with finite-source
models, we need to have access to the finite-source models. Thus, it
would be useful to include them in the ground-motion processing
workspace. This would allow the provenance information to track
updates to a finite-source model as well as alternative finite-source
models for an earthquake.

Additionally, the earthquake rupture model is an important descriptive
feature for scenario (hypothetical) earthquakes. Not only is it useful
to have the finite-source description for computing station metrics,
etc, but we often usually also have multiple realizations that differ
in ways that are not easily described by basic parameters such as
magnitude and hypocenter. Examples include variations in rupture speed
and spatial variation in slip.
