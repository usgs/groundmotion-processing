function peaks = get_waveform_metrics(h5file)
% get_waveform_metrics Retrieve tables of peak ground motions.
%
% See: https://github.com/usgs/groundmotion-processing/#introduction
% 
% Output tables are organized into tables by Intensity Measure Component
% (IMC) - i.e., greater_of_two_horizontals, gmrotd, h1, h2, etc.
% The columns of each table consist of
% event/network/station/location/channel information, plus all of the 
% Intensity Measure Types (IMTs) that were calculated for this ASDF file.
% 
%   waveforms = get_events(h5file)
%   Inputs:
%    - h5file is the path to a ASDF HDF file created by gmprocess.
%   Outputs:
%    - peaks Structure containing tables for each IMC, where table columns are:
%               - network (usually) Two letter network code.
%               - station Station code.
%               - location Location code
%               - channel Name of channel (HNE, HNN, HNZ, etc.)
%               - N columns of IMT values.
%
    peaks = struct;
    hinfo = h5info(h5file);
    for i = 1:length(hinfo.Groups)
        group = hinfo.Groups(i);
        if ~strcmp(group.Name,'/AuxiliaryData')
            continue
        end
        for j=1:length(group.Groups)
            subgroup = group.Groups(j);
            if ~strcmp(subgroup.Name,'/AuxiliaryData/WaveFormMetrics')
                continue
            end
            for k=1:length(subgroup.Groups)
                station = subgroup.Groups(k);
                for m=1:length(station.Datasets)
                    dataset = station.Datasets(m);
                    dname = dataset.Name;
                    parts = regexp(dname,'_','split');
                    nslc = parts{1};
                    eventid = parts{2};
                    parts2 = regexp(nslc,'\.','split');
                    network = parts2{1};
                    scode = parts2{2};
                    lcode = parts2{3};
                    channel = parts2{4};
                    path = strcat(station.Name, '/', dataset.Name);
                    xmlstr = char(h5read(h5file, path))';
                    rows = parse_metrics(xmlstr, eventid, network, scode, lcode, channel);
                    fnames = fieldnames(rows);
                    for n=1:length(fnames)
                        imc = fnames{n};
                        row = rows.(imc);
                        if isfield(peaks,imc)
                            try
                                peaks.(imc) = [peaks.(imc);struct2table(row)];
                            catch me
                                x = 1;
                            end
                        else
                            peaks.(imc) = struct2table(row);
                        end
                    end
                end
            end
        end
    end
end

function rows = parse_metrics(xmlstr, eventid, network, station, location, channel)
    tmpfile = tempname();
    fout = fopen(tmpfile,'wt');
    fwrite(fout, xmlstr);
    fclose(fout);
    rows = struct;
    dom = xmlread(tmpfile);
    metrics = dom.getElementsByTagName('waveform_metrics').item(0);
    imts = metrics.getChildNodes();
    for i=0:imts.getLength()-1
        imt = imts.item(i);
        if imt.getNodeType() ~= imt.ELEMENT_NODE
            continue
        end
        imtstr = char(imt.getNodeName());
        units = char(imt.getAttribute('units'));
        period = '';
        if imt.hasAttribute('period')
            period = str2double(char(imt.getAttribute('period')));
            pname = get_pname(period);
            imtname = sprintf('%s%s',imtstr,pname);
        else
            imtname = imtstr;
        end
        imcs = imt.getChildNodes();
        for j=0:imcs.getLength()-1
            imc = imcs.item(j);
            if imc.getNodeType() ~= imc.ELEMENT_NODE
                continue
            end
            imcname = char(imc.getNodeName());
            imt_value = str2double(imc.getFirstChild.getData());
            if ~isfield(rows, imcname)
                estruct = struct;
                rows = setfield(rows, imcname, estruct);
            end
            rows.(imcname).(imtname) = imt_value;
        end
    end
    for i=0:imcs.getLength()-1
        imc = imcs.item(i);
        if imc.getNodeType() ~= imc.ELEMENT_NODE
            continue
        end
        imcname = char(imc.getNodeName());
        rows.(imcname).('event') = eventid;
        rows.(imcname).('network') = network;
        rows.(imcname).('station') = station;
        rows.(imcname).('location') = location;
        rows.(imcname).('channel') = channel;
    end
    onCleanup(@()delete(tmpfile));
end

function pname = get_pname(period)
    if period < 1
        pname = sprintf('0p%s',strip(num2str(period*1000),'right','0'));
    else
        right = period - floor(period);
        left = floor(period);
        pname = sprintf('%ip%s',left,strip(num2str(right*1000),'right','0'));
        if pname(end) == 'p'
            pname = strcat(pname,'0');
        end
    end
end
