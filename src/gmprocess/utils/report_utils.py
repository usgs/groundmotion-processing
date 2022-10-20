#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import folium
import folium.plugins
from collections import Iterable
from itertools import compress, chain

OCEAN_COLOR = "#96e8ff"
LAND_COLOR = "#ededaf"
PASSED_COLOR = "#00ac00"
FAILED_COLOR = "#ff2222"
EVENT_COLOR = "#FFFF00"  # "#FF0000"
MAP_PADDING = 1.1  # Station map padding value


def draw_stations_map(pstreams, event, event_dir):

    # interactive html map is created first
    lats = np.array([st[0].stats.coordinates["latitude"] for st in pstreams])
    lons = np.array([st[0].stats.coordinates["longitude"] for st in pstreams])
    networks = np.array([st[0].stats.network for st in pstreams])
    stnames = np.array([st[0].stats.station for st in pstreams])
    locs = np.array(
        [
            st[0].stats.location if st[0].stats.location != "" else "N/A"
            for st in pstreams
        ]
    )
    chans = [[tr.stats.channel for tr in st] for st in pstreams]

    failed_st = np.array(
        [np.any([tr.hasParameter("failure") for tr in st]) for st in pstreams]
    )
    failed_tr = np.array(
        [[tr.hasParameter("failure") for tr in st] for st in pstreams], dtype="object"
    )[failed_st]

    failure_reasons = list(
        pd.Series(
            [
                next(tr for tr in st if not tr.passed).getParameter("failure")["reason"]
                for st in pstreams
                if not st.passed
            ],
            dtype=str,
        )
    )

    station_map = folium.Map(
        location=[event.latitude, event.longitude], zoom_start=7, control_scale=True
    )

    # Create feature groups and subgroups so they share cluster behavior
    stn_cluster = folium.plugins.MarkerCluster(name="All", control="False")
    station_map.add_child(stn_cluster)

    passed = folium.plugins.FeatureGroupSubGroup(stn_cluster, "Passed")
    station_map.add_child(passed)

    failed = folium.plugins.FeatureGroupSubGroup(stn_cluster, "Failed")
    station_map.add_child(failed)

    # Extract failed and passed station data
    failed_coords = [list(tup) for tup in zip(lats[failed_st], lons[failed_st])]
    failed_networks = networks[failed_st]
    failed_stations = stnames[failed_st]
    failed_locs = locs[failed_st]
    failed_chans = compress(chans, failed_st)
    failed_station_df = pd.DataFrame(
        {
            "coords": failed_coords,
            "network": failed_networks,
            "stnames": failed_stations,
            "locs": failed_locs,
            "chans": failed_chans,
            "reason": failure_reasons,
        }
    )

    print(failed_locs)

    passed_coords = [list(tup) for tup in zip(lats[~failed_st], lons[~failed_st])]
    passed_networks = networks[~failed_st]
    passed_stations = stnames[~failed_st]
    passed_locs = locs[~failed_st]
    passed_chans = compress(chans, ~failed_st)
    passed_station_df = pd.DataFrame(
        {
            "coords": passed_coords,
            "network": passed_networks,
            "stnames": passed_stations,
            "locs": passed_locs,
            "chans": passed_chans,
        }
    )

    print(passed_locs)

    # Format relevant map data so it can be used Leaflet JS
    failed_map_info = []
    for i, row in enumerate(failed_station_df.values.tolist()):
        new_row = []
        for j, ele in enumerate(row):
            if j < 4:
                if isinstance(ele, list):
                    for sub_ele in ele:
                        new_row.append(sub_ele)
                else:
                    new_row.append(ele)
            elif j == 4:
                comp_colors = []
                for k, comp in enumerate(ele):
                    if failed_tr[i][k]:
                        comp_colors.append(
                            '<span style="color:'
                            + FAILED_COLOR
                            + ';">'
                            + "&nbsp"
                            + str(comp)
                            + "</span>"
                        )
                    else:
                        comp_colors.append(
                            '<span style="color:'
                            + PASSED_COLOR
                            + ';">'
                            + "&nbsp"
                            + str(comp)
                            + "</span>"
                        )

                new_row.append(comp_colors)

            elif j == 5:
                new_row.append(ele)

        failed_map_info.append(new_row)

    # Create Javascript function to pass into Folium for marker cluster creation
    # (Note this callback has to be passed in as a single string)
    # fmt: off
    failed_station_callback = ("""function (row) {
                                var icon = L.divIcon({html: `<div><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill="#ff2222" class="bi bi-triangle-fill" transform="rotate(180)" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/></svg></div>`, className: 'dummy'});
                                var marker = L.marker(new L.LatLng(row[0], row[1]));
                                marker.setIcon(icon);
                                var popup = L.popup({maxWidth: '180', minWidth: '180'});
                                var station_info = $(`<div><b>NETWORK:</b> ${row[2]}<br> <b>STATION:</b> ${row[3]}<br> <b>LOC:</b> ${row[4]}<br> <b>CHAN:</b> ${row[5]} <br> <b>LAT:</b> ${row[0].toFixed(2)}&deg; <b>LON:</b> ${row[1].toFixed(2)}&deg<br> <b>FAILURE MSG:</b><br> <i><span style="color:#ff2222"> ${row[6]} </span></i> </div>`)[0];
                                popup.setContent(station_info);
                                marker.bindPopup(popup);
                                var tooltip = L.tooltip();
                                if (row[4] == "N/A") {var tooltip_info = $(`<div><b>Station:</b> ${row[2]}.<b>${row[3]}</b></div>`)[0];}
                                else {var tooltip_info = $(`<div><b>Station:</b> ${row[2]}.<b>${row[3]}</b>.${row[4]}</div>`)[0];}
                                tooltip.setContent(tooltip_info);
                                marker.bindTooltip(tooltip).openTooltip();
                                return marker};""")
    # fmt: off
    
    # Create station cluster object and add to 'failed' subgroup
    failed_station_cluster = folium.plugins.FastMarkerCluster(
        failed_map_info, callback=failed_station_callback
    )
    failed_station_cluster.add_to(failed)

    # Format relevant map data so it can be used Leaflet JS
    passed_map_info = []
    for row in passed_station_df.values.tolist():
        new_row = []
        for ele in row:
            if isinstance(ele, list):
                for sub_ele in ele:
                    new_row.append(sub_ele)
            else:
                new_row.append(ele)
        passed_map_info.append(new_row)

    # Create Javascript function to pass into Folium for marker cluster creation
    # fmt: off
    passed_station_callback = ("""function (row) {
                                var icon = L.divIcon({html: `<div><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + PASSED_COLOR + """\" class="bi bi-triangle-fill" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/></svg></div>`, className: 'dummy'});
                                var marker = L.marker(new L.LatLng(row[0], row[1]));
                                marker.setIcon(icon);
                                var popup = L.popup({maxWidth: '180', minWidth: '180'});
                                var station_info = $(`<div><b>NETWORK:</b> ${row[2]}<br> <b>STATION:</b> ${row[3]}<br> <b>LOC:</b> ${row[4]}<br> <b>CHAN:</b> ${row[5]}, ${row[6]}, ${row[7]}<br> <b>LAT:</b> ${row[0].toFixed(2)}&deg; <b>LON:</b> ${row[1].toFixed(2)}&deg</div>`)[0];
                                popup.setContent(station_info);
                                marker.bindPopup(popup);
                                var tooltip = L.tooltip();
                                if (row[4] == "N/A") {var tooltip_info = $(`<div><b>Station:</b> ${row[2]}.<b>${row[3]}</b></div>`)[0];}
                                else {var tooltip_info = $(`<div><b>Station:</b> ${row[2]}.<b>${row[3]}</b>.${row[4]}</div>`)[0];}
                                tooltip.setContent(tooltip_info);
                                marker.bindTooltip(tooltip).openTooltip();
                                return marker};""")
    # fmt: on

    # Create station cluster object and add to 'passed' subgroup
    passed_station_cluster = folium.plugins.FastMarkerCluster(
        passed_map_info, callback=passed_station_callback
    )
    passed_station_cluster.add_to(passed)

    # Add the subgroup layers to the map
    folium.LayerControl().add_to(station_map)

    # And finally plot the event itself using just Folium
    event_info = "<b>EVENT ID:</b> {}<br> <b>MAG:</b> {}<br> <b>LAT:</b> {:.4f}&deg; <b>LON:</b> {:.4f}&deg;<br> <b>DEPTH:</b> {:.2f} km".format(
        event.id,
        event.magnitude,
        event.latitude,
        event.longitude,
        (event.depth / 1000.0),
    )
    event_popup = folium.Popup(event_info, min_width=180, max_width=180)

    event_tooltip = folium.Tooltip("<b>EVENT ID:</b> {}".format(event.id))
    event_icon = folium.DivIcon(
        html=f""" 
            <div>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\""""
        + EVENT_COLOR
        + """\" class="bi bi-star-fill" viewBox="0 0 16 16">
                    <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                </svg>
            </div>"""
    )

    folium.Marker(
        [event.latitude, event.longitude],
        tooltip=event_tooltip,
        popup=event_popup,
        fill_color=EVENT_COLOR,
        icon=event_icon,
    ).add_to(station_map)

    station_map.get_root().html.add_child(
        folium.Element(
            """
            <div style="position:absolute; font-family:Noto Sans UI Regular;
                top: 50px; left: 50px; width: 165px; height: 100px; 
                background-color:white; border:2px solid grey;z-index: 900;">

                <div style="padding:5px;">
                    <svg style="vertical-align:center" xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\""""
            + PASSED_COLOR
            + """\" class="bi bi-triangle-fill" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
                    </svg>
                    <text style="padding:5px">Passed Station</text>
                </div>
                
                <div style="padding:5px;">
                    <svg style="vertical-align:center" xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\""""
            + FAILED_COLOR
            + """\" class="bi bi-triangle-fill" transform='rotate(180)' viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
                    </svg>
                    <text style="padding:5px">Failed Station</text>
                </div>

                <div style="padding:5px;">
                    <svg style="vertical-align:center" xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\""""
            + EVENT_COLOR
            + """\" class="bi bi-star-fill" viewBox="0 0 16 16">
                        <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                    </svg>
                    <text style="padding:5px">Earthquake Epicenter</text>
                </div>

            </div>
            """
        )
    )

    html_mapfile = event_dir / "stations_map.html"
    station_map.save(html_mapfile)

    return html_mapfile
