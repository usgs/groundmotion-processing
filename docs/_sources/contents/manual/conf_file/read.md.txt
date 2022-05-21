## Reader Optoins

This is a short section with some options related to reading data. The options
are explained in the comments of the conf file. 

```yaml
read:
    # Look for StationXML files in this directory instead of the `<event>/raw`
    # directory. StationXML file names must follow the convension of 
    # `<network>.<station>.xml`.
    metadata_directory: None

    # Resampling rate if times are unevenly spaced
    resample_rate: 200.0

    # SAC header doesn't include units (!) and is generally assumed to be:
    #     nm/s/s for acceleration
    #     nm/s   for velocity
    #     nm     for displacement
    # The following is a multiplicative factor to convert the SAC data to
    # cm/s/s for accel or cm/s for velocity.
    sac_conversion_factor: 1e-7      # For nm/s/s
    # sac_conversion_factor: 1e-4    # For um/s/s
    # sac_conversion_factor: 980.665 # For g

    # Also, data source is not included in SAC headers, so we provide an option
    # to set it here:
    sac_source: Unknown

    # Group records with the StreamCollection object? This enforces 3 orthogonal 
    # component groupings in which they have the same time span as well as other  
    # consistency checks. Set to False for stuctural/geotech array data for which these
    # do not make sense
    use_streamcollection: True

    # A list of patters SEED patterns to exclude from reading.
    exclude_patterns: ['*.*.??.LN?']
```


% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
