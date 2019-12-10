function waveforms = get_all_waveforms(h5file)
% get_all_waveforms  Retrieve all waveforms from gmprocess ASDF file.
%
% See: https://github.com/usgs/groundmotion-processing/#introduction
% 
%   waveforms = get_all_waveforms(h5file)
%   Inputs:
%    - h5file is the path to a ASDF HDF file created by gmprocess.
%   Outputs:
%    - waveform Structure array, one per waveform:
%               - network (usually) Two letter network code.
%               - station Station code.
%               - location Location code
%               - channel Name of channel (HNE, HNN, HNZ, etc.)
%               - label Processing tag ('unprocessed', 'processed', etc.)
%               - eventid ID of earthquake (us2019abcd, etc.)
%               - starttime Start time of record (Matlab datetime object).
%               - sampling_rate Samples per second.
%               - data Data points of seismic record.
%               - times Arrays of datetimes for each data point.
%

    waveforms = struct([]);
    waveforms(1).network = '';
    waveforms(1).station = '';
    waveforms(1).location = '';
    waveforms(1).channel = '';
    waveforms(1).label = '';
    waveforms(1).eventid = '';
    waveforms(1).starttime = ''; 
    waveforms(1).sampling_rate = '';
    waveforms(1).data = [];
    waveforms(1).times = [];
    started = 0;
    hinfo = h5info(h5file);
    for i = 1:length(hinfo.Groups)
        group = hinfo.Groups(i);
        if strcmp(group.Name,'/Waveforms')
            nwaves = length(group.Groups);
            for j = 1:nwaves
                gname = group.Groups(j).Name;
                for k = 1:length(group.Groups(j).Datasets)
                    dset = group.Groups(j).Datasets(k);
                    dname = dset.Name;
                    if strcmp(dname,'StationXML')
                        continue
                    end
                    % fprintf('Reading dataset %s...\n',dname);
                    parts = regexp(dname,'\.','split');
                    network = parts{1};
                    station = parts{2};
                    location = parts{3};
                    chanparts = regexp(parts{4},'__','split');
                    channel = chanparts{1};
                    endparts = regexp(chanparts{4},'_','split');
                    eventid = endparts{1};
                    label = endparts{2};
                    starttime = nan;
                    sampling_rate = nan;
                    for m = 1:length(dset.Attributes)
                        attr = dset.Attributes(m);
                        if strcmp(attr.Name,'starttime')
                            starttime = attr.Value/1e9;
                            starttime = datetime(starttime,'convertfrom','posixtime');
                        elseif strcmp(attr.Name,'sampling_rate')
                            sampling_rate = attr.Value;
                        end
                    end
                    if ~started
                        idx = 1;
                        started = 1;
                    else
                        idx = length(waveforms) + 1;
                    end
                    waveforms(idx).network = network;
                    waveforms(idx).station = station;
                    waveforms(idx).location = location;
                    waveforms(idx).channel = channel;
                    waveforms(idx).label = label;
                    waveforms(idx).eventid = eventid;
                    waveforms(idx).starttime = starttime;
                    waveforms(idx).sampling_rate = sampling_rate;
                    path = strcat(gname,'/',dname);
                    data = h5read(h5file, path);
                    npts = length(data);
                    dt = npts/sampling_rate * (1/86400);
                    endtime = starttime + dt;
                    times = linspace(starttime, endtime, npts);
                    waveforms(idx).data = data;
                    waveforms(idx).times = times;
                end
            end
        end
    end
end