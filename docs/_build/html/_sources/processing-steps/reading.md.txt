# Reading Data

Triggered Strong motion data can come in many formats, few of which are
familiar to seismologists. Many of the older formats were written using
Fortran, and so are fixed-width, 80 character wide text formats.

`gmprocess` provides readers for many of these formats. Each reader is a package
under the `gmprocess/io` directory in the repository, where that package
contains at least one module called `core.py`, which implements at least two
functions:

 - `is_FORMAT` -- Where FORMAT is the name of the package (knet, geonet, etc.)
   This function returns True if the input file is of that format, False
   otherwise.
 - `read_FORMAT` -- This function returns a list of StationStream objects for
   each file. Some formats contain many channels of data in one file, some only
   have one per file.

`gmprocess` provides a wrapper around all of these readers called `read_data`,
which dynamically discovers the format and attempts to read in the data. Users
should prefer this method of reading in data files.

## Supported Formats

<table>
  <tr>
    <th>Format</th>
    <th>Usual Provider</th>
    <th>Typical Units</th>
    <th>Online Access Available</th>
    <th>Automated Retrieval via gmprocess</th>
  </tr>

  <tr>
    <td>ASDF ( Adaptable Seismic Data Format)</td>
    <td>USGS gmprocess</td>
    <td>any</td>
    <td>No</td>
    <td>No</td>
  </tr>

  <tr>
    <td>RENADIC</td>
    <td><a href="http://terremotos.ing.uchile.cl/">Department of Civil Engineering at the University of Chile</a></td>
    <td>cm/s<sup>2</sup></td>
    <td>Yes</td>
    <td>No</td>
  </tr>

  <tr>
    <td>BHRC</td>
    <td><a href="https://ismn.bhrc.ac.ir/en">Iran Road, Housing & Urban Development Research Center (BHRC)</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>Yes</td>
    <td>No</td>
  </tr>

  <tr>
    <td>COSMOS</td>
    <td><a href="https://strongmotioncenter.org/">Center for Engineering Strong Motion Data (CESMD)</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>Yes</td>
    <td>No</td>
  </tr>

  <tr>
    <td>CWB</td>
    <td><a href="https://www.cwb.gov.tw/eng/">Taiwan Central Weather Bureau (CWB)</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>No</td>
    <td>No</td>
  </tr>

  <tr>
    <td>DMG</td>
    <td><a href="https://strongmotioncenter.org/">Center for Engineering Strong Motion Data (CESMD)</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>Yes</td>
    <td>No</td>
  </tr>

  <tr>
    <td>FDSN*</td>
    <td><a href="http://www.fdsn.org/networks/">International Federation of Digital Seismograph Networks (FDSN)</a></td>
    <td>counts (gals)</td>
    <td>Yes</td>
    <td>Yes</td>
  </tr>

  <tr>
    <td>GEONET</td>
    <td><a href="https://www.geonet.org.nz/">New Zealand GeoNet</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>Yes</td>
    <td>Yes</td>
  </tr>

  <tr>
    <td>KNET/KIKNET</td>
    <td><a href="http://www.kyoshin.bosai.go.jp/">Japanese National Research Institute for Earth Science and Disaster Resilience</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>Yes</td>
    <td>Yes</td>
  </tr>

  <tr>
    <td>NSMN</td>
    <td><a href="http://kyhdata.deprem.gov.tr/2K/kyhdata_v4.php">National Strong-Motion Network of Turkey (TR-NSMN)</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>Yes</td>
    <td>Yes</td>
  </tr>

  <tr>
    <td>SMC</td>
    <td><a href="https://strongmotioncenter.org/">Center for Engineering Strong Motion Data (CESMD)</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>Yes</td>
    <td>No</td>
  </tr>

  <tr>
    <td>USC</td>
    <td><a href="https://strongmotioncenter.org/">Center for Engineering Strong Motion Data (CESMD)</a></td>
    <td>cm/s<sup>2</sup> (gals)</td>
    <td>Yes</td>
    <td>No</td>
  </tr>

</table>

The FDSN "format" consists of:
1) Any Obspy supported format (SAC, MiniSEED, etc.) and
2) A StationXML file containing station/sensor response information.

## Sample Usage

```python
import glob
from gmprocess.io.read import read_data

# these sample files can be found in the repository
# under gmprocess/data/testdata/knet/us2000cnnl
# knet files are stored one channel per file.
datafiles = glob.glob('AOM0011801241951.*')
streams = []
for datafile in datafiles:
  streams += read_data(datafile)
```

For users that need to know more about the formats of the files they are
reading, the command line program `gminfo` distributed with gmprocess can be
used to inspect the files before attempting to read them.
