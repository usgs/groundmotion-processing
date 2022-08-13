#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
import pandas as pd
import folium

OCEAN_COLOR = "#96e8ff"
LAND_COLOR = "#ededaf"
PASSED_COLOR = "#00ac00"
FAILED_COLOR = "#ff2222"
EVENT_COLOR = "#FFFF00" #"#FF0000"
MAP_PADDING = 1.1  # Station map padding value


def draw_stations_map(pstreams, event, event_dir):

    # interactive html map is created first
    lats = np.array([stream[0].stats.coordinates["latitude"] for stream in pstreams])
    lons = np.array([stream[0].stats.coordinates["longitude"] for stream in pstreams])
    stnames = np.array([stream[0].stats.station for stream in pstreams])
    networks = np.array([stream[0].stats.network for stream in pstreams])

    failed = np.array(
        [
            np.any([trace.hasParameter("failure") for trace in stream])
            for stream in pstreams
        ]
    )

    failure_reasons = list(
        pd.Series(
            [
                next(tr for tr in st if tr.hasParameter("failure")).getParameter(
                    "failure"
                )["reason"]
                for st in pstreams
                if not st.passed
            ],
            dtype=str,
        )
    )

    station_map = folium.Map(
        location=[event.latitude, event.longitude], zoom_start=7, control_scale=True
    )

    failed_coords = zip(lats[failed], lons[failed])
    failed_stations = stnames[failed]
    failed_networks = networks[failed]
    failed_station_df = pd.DataFrame(
        {
            "stnames": failed_stations,
            "network": failed_networks,
            "coords": failed_coords,
            "reason": failure_reasons,
        }
    )

    passed_coords = zip(lats[~failed], lons[~failed])
    passed_stations = stnames[~failed]
    passed_networks = networks[~failed]
    passed_station_df = pd.DataFrame(
        {
            "stnames": passed_stations,
            "network": passed_networks,
            "coords": passed_coords,
        }
    )

    # Plot the failed first
    for i, r in failed_station_df.iterrows():
        station_info = "<b>NETWORK:</b> {}<br> <b>LAT:</b> {:.4f}&deg; <b>LON:</b> {:.4f}&deg;<br> <b>FAILURE MSG:</b><br> <i>'{}'</i>".format(
            r["network"], r["coords"][0], r["coords"][1], r["reason"]
        ) 
        failed_popup = folium.Popup(station_info,
            min_width=250,
             max_width=250)

        failed_tooltip= folium.Tooltip("<b>Station:</b> {}".format(
            r["stnames"])
        )

        failed_icon = folium.DivIcon(html=f""" 
            <div>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill="#ff2222" class="bi bi-triangle-fill" transform='rotate(180)' viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
                </svg>
            </div>""")

        folium.Marker(
            location=r["coords"],
            tooltip=failed_tooltip,
            popup=failed_popup,
            icon=failed_icon).add_to(station_map)

    # Then the passed stations
    for i, r in passed_station_df.iterrows():
        station_info = "<b>NETWORK:</b> {}<br> <b>LAT:</b> {:.4f}&deg; <b>LON:</b> {:.4f}&deg;".format(
            r["network"], r["coords"][0], r["coords"][1]
        )

        passed_popup = folium.Popup(station_info,
            min_width=180,
            max_width=180)

        passed_tooltip = folium.Tooltip("<b>Station:</b> {}".format(
            r["stnames"])
        )

        passed_icon = folium.DivIcon(html=f""" 
            <div>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + PASSED_COLOR + """\" class="bi bi-triangle-fill" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
                </svg>
            </div>""")

        folium.Marker(
            location=r["coords"],
            tooltip=passed_tooltip,
            popup=passed_popup,
            icon=passed_icon).add_to(station_map)

    # And finally the event itself
    event_info = "<b>EVENT ID:</b> {}<br> <b>MAG:</b> {}<br> <b>LAT:</b> {:.4f}&deg; <b>LON:</b> {:.4f}&deg;<br> <b>DEPTH:</b> {:.2f} km".format(
        event.id,  event.magnitude, event.latitude, event.longitude, (event.depth/1000.0)
    )
    event_popup = folium.Popup(event_info,
            min_width=180,
            max_width=180)

    event_tooltip = folium.Tooltip("<b>EVENT ID:</b> {}".format(
        event.id)
    )
    event_icon = folium.DivIcon(html=f""" 
            <div>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + EVENT_COLOR + """\" class="bi bi-star-fill" viewBox="0 0 16 16">
                    <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                </svg>
            </div>""")

    folium.Marker(
        [event.latitude, event.longitude],
        tooltip=event_tooltip,
        popup=event_popup,
        fill_color=EVENT_COLOR,
        icon=event_icon).add_to(station_map)
    
    station_map.get_root().html.add_child(
        folium.Element(
            """
            <div style="position:absolute; font-family:Noto Sans UI Regular;
                top: 50px; left: 50px; width: 165px; height: 100px; 
                background-color:white; border:2px solid grey;z-index: 900;">

                <div style="padding:5px;">
                    <svg style="vertical-align:center" xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + FAILED_COLOR + """\" class="bi bi-triangle-fill" transform='rotate(180)' viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
                    </svg>
                    <text style="padding:5px">Passed Station</text>
                </div>
                
                <div style="padding:5px;">
                    <svg style="vertical-align:center" xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + PASSED_COLOR + """\" class="bi bi-triangle-fill" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
                    </svg>
                    <text style="padding:5px">Failed Station</text>
                </div>

                <div style="padding:5px;">
                    <svg style="vertical-align:center" xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + EVENT_COLOR + """\" class="bi bi-star-fill" viewBox="0 0 16 16">
                        <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                    </svg>
                    <text style="padding:5px">Earthquake Epicenter</text>
                </div>

            </div>
            """
        )
    )

    html_mapfile = os.path.join(event_dir, "stations_map.html")
    station_map.save(html_mapfile)

    return (html_mapfile)
