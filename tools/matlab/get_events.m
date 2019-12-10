function events = get_events(h5file)
%get_events Return information about events in ASDF workspace file.
%
% See: https://github.com/usgs/groundmotion-processing/#introduction
% 
%   waveforms = get_events(h5file)
%   Inputs:
%    - h5file is the path to a ASDF HDF file created by gmprocess.
%   Outputs:
%    - events Structure array, one per earthquake:
%               - eventid Event id (i.e., '2019abcd')
%               - time Matlab datenum of origin time
%               - latitude Latitude of earthquake
%               - longitude Longitude of earthquake
%               - depth Depth of earthquake (km)
%               - magnitude Magnitude of earthquake
%
    xmlstr = char(h5read(h5file,'/QuakeML'))';
    tmpfile = tempname();
    fout = fopen(tmpfile,'wt');
    fwrite(fout, xmlstr);
    fclose(fout);
    
    dom = xmlread(tmpfile);
    events = struct([]);
    events(1).eventid = '';
    events(1).time = '';
    events(1).latitude = '';
    events(1).longitude = '';
    events(1).depth = '';
    events(1).magnitude = '';
    
    event_objs = dom.getElementsByTagName('event');
    for i=0:event_objs.getLength-1
        eventroot = event_objs.item(i);
        eventid_str = char(eventroot.getAttribute('publicID'));
        ecells = regexp(eventid_str, '/', 'split');
        eventid = char(ecells{2});
        origin = eventroot.getElementsByTagName('origin').item(0);
        time = origin.getElementsByTagName('time').item(0);
        timestr = char(time.getElementsByTagName('value').item(0).getFirstChild.getData());
        dtime = datenum(timestr(1:19),'yyyy-mm-ddTHH:MM:SS');
        latitude = origin.getElementsByTagName('latitude').item(0);
        lat = str2double(char(latitude.getElementsByTagName('value').item(0).getFirstChild.getData()));
        longitude = origin.getElementsByTagName('longitude').item(0);
        lon = str2double(char(longitude.getElementsByTagName('value').item(0).getFirstChild.getData()));
        depth = origin.getElementsByTagName('depth').item(0);
        dep = str2double(char(depth.getElementsByTagName('value').item(0).getFirstChild.getData()));
        dep = dep/1000;
        magnitude = eventroot.getElementsByTagName('magnitude').item(0);
        mag = str2double(char(magnitude.getElementsByTagName('value').item(0).getFirstChild.getData()));
        events(i+1).eventid = eventid;
        events(i+1).time = dtime;
        events(i+1).latitude = lat; 
        events(i+1).longitude = lon; 
        events(i+1).depth = dep; 
        events(i+1).magnitude = mag; 
    end
    onCleanup(@()delete(tmpfile));
end

