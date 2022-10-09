# Unit test data

This file describes the mapping between the data in this directory and the unit tests that use these data.

arias_data.json
  - tests/gmprocess/metrics/imt/arias_test.py

## asdf/ [2.8M]
asdf/asdf_layout.txt
  - tests/gmprocess/io/asdf/asdf_layout_test.py
asdf/nc71126864
  - tests/gmprocess/io/cosmos/writer_test.py

## bhrc/ [2.8M]
bhrc/usp000jq5p
  - tests/gmprocess/io/bhrc/bhrc_test.py

## clipping_samples/ [2.7M]
clipping_samples/hv70907436
  - tests/gmprocess/waveform_processing/clipping/clipping_check_test.py
  - tests/gmprocess/waveform_processing/clipping/histogram_test.py
  - tests/gmprocess/waveform_processing/clipping/jerk_test.py
  - tests/gmprocess/waveform_processing/clipping/max_amp_test.py
  - tests/gmprocess/waveform_processing/clipping/ping_test.py
  - tests/gmprocess/waveform_processing/clipping/std_dev_test.py

## colocated_instruments/ [2.1M]
colocated_instruments
  - tests/gmprocess/core/colocated_test.py

config_min_freq_0p2.yml
  - tests/gmprocess/io/asdf/asdf_layout_test.py
  - tests/gmprocess/io/asdf/stream_workspace_test.py
  - tests/gmprocess/waveform_processing/processing_test.py

## cosmos/ [1.7M]
cosmos/ak018fcnsk91
  - tests/gmprocess/io/cosmos/cosmos_test.py
cosmos/ci14155260
  - tests/gmprocess/io/cosmos/cosmos_test.py
  - tests/gmprocess/io/read_test.py
cosmos/ftbragg
  - tests/gmprocess/io/cosmos/cosmos_test.py
cosmos/us1000hyfh
  - tests/gmprocess/io/cosmos/cosmos_test.py
  - tests/gmprocess/metrics/imt/duration_test.py
  - tests/gmprocess/metrics/imt/sorted_duration_test.py

## csn/ [184K]
csn/ci38457511
  - tests/gmprocess/io/obspy/obspy_test.py

## cwb/ [1.2M]
cwb/us1000chhc
  - tests/gmprocess/io/read_test.py
  - tests/gmprocess/io/stream_test.py
  - tests/gmprocess/io/cwb/cwb_test.py
  - tests/gmprocess/io/dmg/dmg_test.py
  - tests/gmprocess/metrics/imt/arias_test.py
  - tests/gmprocess/metrics/imt/duration_test.py
  - tests/gmprocess/utils/plot_test.py
  - tests/gmprocess/waveform_processing/phase_test.py

## demo/ [4.0M]
demo/ci38038071
  - tests/gmprocess/subcommands/assemble_test.py
demo/ci38457511
  - tests/gmprocess/subcommands/assemble_test.py

## demo_steps/ [50M]
demo_steps/compute_metrics
  - tests/gmprocess/subcommands/compute_station_metrics_test.py
  - tests/gmprocess/subcommands/compute_waveform_metrics_test.py
demo_steps/exports
  - tests/gmprocess/subcommands/export_failures_test.py
  - tests/gmprocess/subcommands/export_metric_tables_test.py
  - tests/gmprocess/subcommands/export_provenance_tables_test.py
  - tests/gmprocess/subcommands/export_shakemap_test.py
  - tests/gmprocess/subcommands/generate_regression_plot_test.py
demo_steps/process_waveforms
  - tests/gmprocess/subcommands/process_waveforms_test.py

## dmg/ [7.1M]
dmg/ci15481673
  - tests/gmprocess/io/dmg/dmg_test.py
dmg/ci3031425
  - tests/gmprocess/io/utils_test.py
  - tests/gmprocess/io/dmg/dmg_test.py
dmg/ci3144585
  - tests/gmprocess/core/streamarray_test.py
  - tests/gmprocess/core/streamcollection_test.py
  - tests/gmprocess/io/dmg/dmg_test.py
dmg/nc1091100
  - tests/gmprocess/io/dmg/dmg_test.py
dmg/nc71734741
  - tests/gmprocess/io/read_test.py
  - tests/gmprocess/io/dmg/dmg_test.py
dmg/nc72282711
  - tests/gmprocess/io/dmg/dmg_test.py

## duplicate/ [16M]
duplicate/alaska
  - tests/gmprocess/core/streamcollection_test.py
duplicate/general
  - tests/gmprocess/core/streamcollection_test.py
  - tests/gmprocess/io/smc/smc_test.py
duplicate/hawaii
  - tests/gmprocess/core/streamcollection_test.py

duration_data.json
  - tests/gmprocess/metrics/imt/duration_test.py

events.xlsx
  - tests/gmprocess/utils/plot_test.py

fas_arithmetic_mean.pkl
  - tests/gmprocess/metrics/imt/fas_arithmetic_mean_test.py

fas_channels.pkl
  - tests/gmprocess/metrics/imt/fas_channels_test.py

fas_geometric_mean.pkl
  - tests/gmprocess/metrics/imt/fas_geometric_mean_test.py

fas_greater_of_two_horizontals.pkl
  - tests/gmprocess/metrics/imt/fas_greater_of_two_test.py

fas_quadratic_mean.pkl
  - tests/gmprocess/metrics/imt/fas_quadratic_mean_test.py

## fdsn/ [4.5M]
fdsn/test_config.yml
  - tests/gmprocess/io/asdf/stream_workspace_test.py
fdsn/ci38445975
  - tests/gmprocess/io/asdf/stream_workspace_test.py
  - tests/gmprocess/io/obspy/obspy_test.py
fdsn/ci38457511
  - tests/gmprocess/io/asdf/stream_workspace_test.py
  - tests/gmprocess/waveform_processing/windows_test.py
fdsn/nc51194936
  - tests/gmprocess/waveform_processing/processing_test.py
fdsn/nc72282711
  - tests/gmprocess/io/obspy/obspy_test.py
  - tests/gmprocess/io/unam/unam_test.py
fdsn/nc73300395
  - tests/gmprocess/io/obspy/obspy_test.py
fdsn/se60247871
  - tests/gmprocess/io/obspy/obspy_test.py
fdsn/us70008dx7
  - tests/gmprocess/io/obspy/obspy_test.py
fdsn/uu60363602
  - tests/gmprocess/metrics/stationsummary_test.py
fdsn/uw61251926
  - tests/gmprocess/core/stastream_test.py

## fdsnfetch/ [1.3M]
fdsnfetch/inventory.xml
  - tests/gmprocess/metrics/imc/radial_transverse_test.py
fdsnfetch/inventory_sew.xml
  - tests/gmprocess/metrics/imc/radial_transverse_test.py
fdsnfetch/raw/resp_cor
  - tests/gmprocess/metrics/imc/radial_transverse_test.py

## geonet/ [6.6M]
geonet/nz2018p115908
  - tests/gmprocess/io/stream_test.py
  - tests/gmprocess/io/asdf/stream_workspace_test.py
  - tests/gmprocess/io/esm/esm_test.py
  - tests/gmprocess/io/geonet/geonet_test.py
  - tests/gmprocess/io/knet/knet_test.py
geonet/us1000778i
  - tests/gmprocess/io/read_test.py
  - tests/gmprocess/io/stream_test.py
  - tests/gmprocess/io/asdf/asdf_layout_test.py
  - tests/gmprocess/io/asdf/asdf_test.py
  - tests/gmprocess/io/asdf/stream_workspace_test.py
  - tests/gmprocess/io/geonet/geonet_test.py
  - tests/gmprocess/metrics/metrics_controller_test.py
  - tests/gmprocess/metrics/oscillators_test.py
  - tests/gmprocess/metrics/peak_time_test.py
  - tests/gmprocess/metrics/stationsummary_test.py
  - tests/gmprocess/metrics/imc/channels_test.py
  - tests/gmprocess/metrics/imc/gmrotd_test.py
  - tests/gmprocess/metrics/imc/greater_of_two_horizontals_test.py
  - tests/gmprocess/metrics/imc/rotd_test.py
  - tests/gmprocess/metrics/imt/pga_test.py
  - tests/gmprocess/metrics/imt/pgv_test.py
  - tests/gmprocess/metrics/imt/sa_test.py
  - tests/gmprocess/waveform_processing/adjust_highpass_ridder_test.py
  - tests/gmprocess/waveform_processing/baseline_correction_test.py
  - tests/gmprocess/waveform_processing/corner_frequencies_test.py
  - tests/gmprocess/waveform_processing/integrate_test.py
  - tests/gmprocess/waveform_processing/nn_quality_assurance_test.py
  - tests/gmprocess/waveform_processing/phase_test.py
  - tests/gmprocess/waveform_processing/processing_test.py

greater_of_two_horizontals.xlsx
  - tests/gmprocess/utils/plot_test.py

## high_freq_sa/ [2.0M]
  - tests/gmprocess/metrics/high_freq_test.py

## import/ [6.8M]
import/cesmd_test.zip
  - tests/gmprocess/subcommands/import_test.py
import/dir
  - tests/gmprocess/subcommands/import_test.py
import/test.tar
  - tests/gmprocess/subcommands/import_test.py

## kiknet/ [2.0M]
kiknet/usp000a1b0
  - tests/gmprocess/io/stream_test.py
  - tests/gmprocess/io/knet/knet_test.py
kiknet/usp000hzq8
  - tests/gmprocess/waveform_processing/processing_test.py

## knet/ [3.1M]
knet/us2000cnnl
  - tests/gmprocess/io/read_test.py
  - tests/gmprocess/io/stream_test.py
  - tests/gmprocess/io/knet/knet_test.py
  - tests/gmprocess/waveform_processing/windows_test.py
knet/usb000syza
  - tests/gmprocess/io/asdf/stream_workspace_test.py

## lowpass_max/ [80K]
  - tests/gmprocess/waveform_processing/lowpass_max_test.py

## metrics_controller/ [12K]
  - tests/gmprocess/metrics/metrics_controller_test.py

## multiple_events/ [3.5M]
multiple_events/catalog.csv
  - tests/gmprocess/waveform_processing/windows_test.py
multiple_events/ci38457511
  - tests/gmprocess/waveform_processing/windows_test.py

## nsmn/ [4.3M]
nsmn/us20009ynd
  - tests/gmprocess/io/nsmn/nsmn_test.py
  - tests/gmprocess/waveform_processing/phase_test.py

## peer/ [240K]
  - tests/gmprocess/metrics/imt/fas_arithmetic_mean_test.py
  - tests/gmprocess/metrics/imt/fas_channels_test.py
  - tests/gmprocess/metrics/imt/fas_geometric_mean_test.py
  - tests/gmprocess/metrics/imt/fas_greater_of_two_test.py
  - tests/gmprocess/metrics/imt/fas_quadratic_mean_test.py

## process/ [2.8M]
  - tests/gmprocess/metrics/rotation_test.py
  - tests/gmprocess/metrics/imc/rotd_test.py
  - tests/gmprocess/waveform_processing/phase_test.py
  - tests/gmprocess/waveform_processing/windows_test.py

## read_directory/ [664K]
  - tests/gmprocess/io/read_directory_test.py

## renadic/ [18M]
  - tests/gmprocess/io/renadic/renadic_test.py

## smc/ [7.9M]
smc/nc216859
  - tests/gmprocess/io/read_test.py
  - tests/gmprocess/io/stream_test.py
  - tests/gmprocess/io/smc/smc_test.py
  - tests/gmprocess/io/usc/usc_test.py

## station_xml_epochs/ [616K]
station_xml_epochs/nc73631381
  - tests/gmprocess/io/obspy/stastionxml_test.py
station_xml_epochs/nc73631381_ad
  - tests/gmprocess/io/obspy/stastionxml_test.py

## status/ [1.4M]
  - tests/gmprocess/core/streamcollection_test.py

strong-motion.mat
  - tests/gmprocess/waveform_processing/phase_test.py

## travel_times/ [520K]
travel_times/catalog_test_traveltimes.csv
  - tests/gmprocess/waveform_processing/phase_test.py
travel_times/ci37218996
  - tests/gmprocess/waveform_processing/phase_test.py
travel_times/ci38461735
  - tests/gmprocess/waveform_processing/phase_test.py

## tutorials/ [3.0M]
  - ../../doc_source/

## unam/ [4.5M]
unam/us2000ar20
  - tests/gmprocess/io/unam/unam_test.py
unam/usp000cgtd
  - tests/gmprocess/io/unam/unam_test.py

## usc/ [848K]
usc/ci3144585
  - tests/gmprocess/core/streamarray_test.py
  - tests/gmprocess/core/streamcollection_test.py
  - tests/gmprocess/io/nga_test.py
  - tests/gmprocess/io/stream_test.py
  - tests/gmprocess/io/usc/usc_test.py

usp000hat0_quakeml.xml
  - tests/gmprocess/utils/event_test.py

vcr_event_test.yaml
  - tests/gmprocess/utils/event_test.py

## zero_crossings/ [40K]
  - tests/gmprocess/waveform_processing/zero_crossings_test.py
