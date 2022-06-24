## Handling Duplicates

This section is for handling duplicate data when creating a StreamCollection.
Stations are classified as duplicates in a somewhat complex manner. The reason
for this is that a more straight forward approach based solely on network, 
station, and channel codes is not possible because some data formats do not 
provide network codes. Thus, we determine whether two StationTraces are 
duplicates by checking the station, channel codes, and the distance between 
them.

```yaml
duplicate:
    # This section is for handling duplicate data when creating a StreamCollection

    # Maximum distance tolerance (in m) for duplicate data
    max_dist_tolerance: 500.0

    # List of preferences (in order) for handling duplicate data.
    preference_order: ['process_level', 'source_format', 'starttime', 'npts',
                       'sampling_rate', 'location_code']

    # Preference for selecting process level when faced with duplicate data
    # but with different processing levels. Must be a list containing
    # 'V0', 'V1', and 'V2'. The first item is the most preferred,
    # and the last item is the least preferred.
    process_level_preference: ['V1', 'V0', 'V2']

    # Preference for selecting the format when faced with duplicate data
    # but with different source formats. Must be a list containing the source
    # format abbreviations found in gmprocess.io. Does not need to contain
    # all possible formats.

    # Example to always prefer COSMOS files over DMG files
    format_preference: ['cosmos', 'dmg']
```


% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`
