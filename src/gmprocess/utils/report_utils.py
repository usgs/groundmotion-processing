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
    stnames = np.array([st[0].stats.station for st in pstreams])
    chans = [[tr.stats.channel for tr in st] for st in pstreams]
    networks = np.array([st[0].stats.network for st in pstreams])

    failed_st = np.array(
        [np.any([tr.hasParameter("failure") for tr in st]) for st in pstreams]
    )
    failed_tr = np.array(
        [[tr.hasParameter("failure") for tr in st] for st in pstreams],
         dtype='object'
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
    stations_group = folium.FeatureGroup(name='stations')

    # failed_coords = zip(lats[failed_st], lons[failed_st])
    failed_coords = [list(tup) for tup in zip(lats[failed_st], lons[failed_st])]
    failed_stations = stnames[failed_st]
    failed_chans = compress(chans,failed_st)
    failed_networks = networks[failed_st]
    failed_station_df = pd.DataFrame(
        {
            "stnames": failed_stations,
            "chans": failed_chans,
            "network": failed_networks,
            "coords": failed_coords,
            "reason": failure_reasons,
        }
    )

    # passed_coords = zip(lats[~failed_st], lons[~failed_st])
    # passed_coords = [list(tup) for tup in zip(lats[~failed_st], lons[~failed_st])]
    # passed_stations = stnames[~failed_st]
    # passed_chans = compress(chans, ~failed_st)
    # passed_networks = networks[~failed_st]
    # passed_station_df = pd.DataFrame(
    #     {
    #         "stnames": passed_stations,
    #         "chans": passed_chans,
    #         "network": passed_networks,
    #         "coords": passed_coords,
    #     }
    # )
    passed_coords = [list(tup) for tup in zip(lats[~failed_st], lons[~failed_st])]
    passed_stations = stnames[~failed_st]
    passed_chans = compress(chans, ~failed_st)
    passed_networks = networks[~failed_st]
    passed_station_df = pd.DataFrame(
        {
            "coords": passed_coords,
            "stnames": passed_stations,
            "chans": passed_chans,
            "network": passed_networks,        }
    )
    # # Plot the failed first
    # for i, r in failed_station_df.iterrows():
    #     chan_fmt = []
    #     for j,fail in enumerate(failed_tr[i]):
    #         if fail:
    #             chan_fmt.append("<span style=\"color:" + FAILED_COLOR + ";\">" + str(r["chans"][j]) + "</span>")
    #         else:
    #             chan_fmt.append("<span style=\"color:" + PASSED_COLOR + ";\">" + str(r["chans"][j]) + "</span>")

    #     chan_info = "<b>CHAN:</b> {}".format(
    #         ', '.join(chan_fmt)
    #     )

    #     fail_info = "<b>FAILURE MSG:</b><br> <i>'{}'</i>".format(
    #         "<span style=\"color:" + FAILED_COLOR + ";\">" + r["reason"] + "</span>"
    #     )

    #     station_info = "<b>NETWORK:</b> {}<br> <b>STATION:</b> {}<br> {}<br> <b>LAT:</b> {:.4f}&deg; <b>LON:</b> {:.4f}&deg;<br> {}".format(
    #         r["network"], r["stnames"], chan_info, r["coords"][0], r["coords"][1], fail_info
    #     ) 

    #     failed_popup = folium.Popup(station_info, min_width=250, max_width=250)

    #     failed_tooltip = folium.Tooltip(f"<b>Station:</b> {r['network']}.{r['stnames']}")

    #     failed_icon = folium.DivIcon(
    #         html=f""" 
    #         <div>
    #             <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill="#ff2222" class="bi bi-triangle-fill" transform='rotate(180)' viewBox="0 0 16 16">
    #                 <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
    #             </svg>
    #         </div>"""
    #     )

    #     folium.Marker(
    #         location=r["coords"],
    #         tooltip=failed_tooltip,
    #         popup=failed_popup,
    #         icon=failed_icon,
    #     ).add_to(station_map)

    # # Then the passed stations
    # for i, r in passed_station_df.iterrows():
    #     chan_info = ", ".join(r["chans"])

        failed_tooltip = folium.Tooltip(
            f"<b>Station:</b> {r['network']}.{r['stnames']}"
        )

    #     passed_popup = folium.Popup(station_info, min_width=180, max_width=180)

    #     passed_tooltip = folium.Tooltip(f"<b>Station:</b> {r['network']}.{r['stnames']}")

    #     passed_icon = folium.DivIcon(
    #         html=f""" 
    #         <div>
    #             <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\""""
    #         + PASSED_COLOR
    #         + """\" class="bi bi-triangle-fill" viewBox="0 0 16 16">
    #                 <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
    #             </svg>
    #         </div>"""
    #     )

    #     folium.Marker(
    #         location=r["coords"],
    #         tooltip=passed_tooltip,
    #         popup=passed_popup,
    #         icon=passed_icon,
    #     ).add_to(station_map)

    passed_map_info = []
    for i, r in passed_station_df.iterrows():
        chan_info = ", ".join(r["chans"])

        station_info = "<b>NETWORK:</b> {}<br> <b>STATION:</b> {}<br> <b>CHAN:</b> {}<br> <b>LAT:</b> {:.4f}&deg; <b>LON:</b> {:.4f}&deg;".format(
            r["network"], r["stnames"], chan_info, r["coords"][0], r["coords"][1]
        )

        passed_popup = folium.Popup(station_info, min_width=180, max_width=180)

        passed_tooltip = folium.Tooltip(f"<b>Station:</b> {r['network']}.{r['stnames']}")

    # callback = ('function (row) {' 
    #                 'var marker = L.marker(new L.LatLng(row[0], row[1]), {color: "red"});'
    #                 'var icon = L.AwesomeMarkers.icon({'
    #                 "icon: 'info-sign',"
    #                 "iconColor: 'white',"
    #                 "markerColor: 'green',"
    #                 "prefix: 'glyphicon',"
    #                 "extraClasses: 'fa-rotate-0'"
    #                     '});'
    #                 'marker.setIcon(icon);'
    #                 "var popup = L.popup({maxWidth: '300'});"
    #                 "const display_text = {text: row[2]};"
    #                 "var mytext = $(`<div id='mytext' class='display_text' style='width: 100.0%; height: 100.0%;'> ${display_text.text}</div>`)[0];"
    #                 "popup.setContent(mytext);"
    #                 "marker.bindPopup(popup);"
    #                 'return marker};')    


    failed_station_callback = ("""function (row) {
                                var icon = L.divIcon({html: `<div><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill="#ff2222" class="bi bi-triangle-fill" transform="rotate(180)" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/></svg></div>`, className: 'dummy'});
                                var marker = L.marker(new L.LatLng(row[0], row[1]));
                                marker.setIcon(icon);
                                var popup = L.popup({maxWidth: '180', minWidth: '180'});
                                const display_text = {text: 'beep boop'};
                                var mytext = $(`<div id='mytext' class='display_text' style='width: 100.0%; height: 100.0%;'> ${display_text.text}</div>`)[0];
                                popup.setContent(mytext);
                                marker.bindPopup(popup);
                                return marker};""")
    # print(failed_station_df["coords"].values.tolist())
    failed_station_cluster = folium.plugins.FastMarkerCluster(failed_station_df["coords"].values.flatten().tolist(), callback=failed_station_callback)
    stations_group.add_child(failed_station_cluster)
    # station_map.add_child(folium.plugins.FastMarkerCluster(failed_station_df["coords"].values.flatten().tolist(), callback=failed_station_callback))

    # passed_station_callback = ("""function (row) {
    #                             var icon = L.divIcon({html: `<div><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + PASSED_COLOR + """\" class="bi bi-triangle-fill" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/></svg></div>`});
    #                             var marker = L.marker(new L.LatLng(row[0], row[1]));
    #                             marker.setIcon(icon);
    #                             var popup = L.popup({maxWidth: '180', minWidth: '180'});
    #                             const display_text = {text: row[2]};
    #                             var mytext = $(`<div id='mytext' class='display_text' style='width: 100.0%; height: 100.0%;'> ${display_text.text}</div>`)[0];
    #                             popup.setContent(mytext);
    #                             marker.bindPopup(popup);
    #                             return marker};""")

    # station_map.add_child(folium.plugins.FastMarkerCluster(passed_station_df["coords"].values.tolist(), callback=passed_station_callback))
    passed_station_callback = ("""function (row) {
                                var icon = L.divIcon({html: `<div><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + PASSED_COLOR + """\" class="bi bi-triangle-fill" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/></svg></div>`, className: 'dummy'});
                                var marker = L.marker(new L.LatLng(row[0], row[1]));
                                marker.setIcon(icon);
                                var popup = L.popup({maxWidth: '180', minWidth: '180'});
                                const display_text = {text: 'boop beep'};
                                var mytext = $(`<div id='mytext' class='display_text' style='width: 100.0%; height: 100.0%;'> ${display_text.text}</div>`)[0];
                                popup.setContent(mytext);
                                marker.bindPopup(popup);
                                return marker};""")
    
    map_info = passed_station_df.values.tolist()
    print(map_info)
    # test = [row.values.ravel().tolist() for i,row in passed_station_df.iterrows()]
    # test = [dat.values.ravel().tolist() for i,row in passed_station_df.iterrows() for dat in row]
    # test = list(chain.from_iterable(passed_station_df.values.tolist()))
    # test = list(chain.from_iterable(*passed_station_df.values.tolist()))
    # test = [list(chain.from_iterable(row)) for row in passed_station_df.values.tolist()]
    # test = list(chain.from_iterable(item if isinstance(item,list) and
                    # not isinstance(item, str) else list(item) for item in passed_station_df.values.tolist()))
    # print(test)

    test2 = []
    for row in passed_station_df.values.tolist():
        new_row = []
        for ele in row:
            if isinstance(ele,list):
                # new_ele = chain.from_iterable(ele)
                # new_row.append(new_ele)
                for sub_ele in ele:
                    new_row.append(sub_ele)
            else:
                new_row.append(ele)
        test2.append(new_row)
    print(test2)      
    map_info = test2
    passed_station_cluster = folium.plugins.FastMarkerCluster(map_info, callback=passed_station_callback)
    stations_group.add_child(passed_station_cluster)
    # station_map.add_child(folium.plugins.FastMarkerCluster(map_info, callback=passed_station_callback))

    station_map.add_child(stations_group)

    # And finally the event itself
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
