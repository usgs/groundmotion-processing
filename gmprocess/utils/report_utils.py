#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
import pandas as pd
import folium
from folium import plugins
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from impactutils.mapping.city import Cities
from impactutils.mapping.mercatormap import MercatorMap
from impactutils.mapping.scalebar import draw_scale
from cartopy import feature as cfeature


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
        station_info = "NET: {} LAT: {:.2f} LON: {:.2f} REASON: {}".format(
            r["network"], r["coords"][0], r["coords"][1], r["reason"]
        ) 
  
        failed_icon = folium.DivIcon(html=f""" 
            <div>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill="#ff2222" class="bi bi-triangle-fill" transform='rotate(180)' viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
                </svg>
            </div>""")

        folium.Marker(
            location=r["coords"],
            tooltip=r["stnames"],
            popup=station_info,
            icon=failed_icon).add_to(station_map)

    # Then the passed stations
    for i, r in passed_station_df.iterrows():
        station_info = "NET: {}\n LAT: {:.2f} LON: {:.2f}".format(
            r["network"], r["coords"][0], r["coords"][1]
        )
        passed_icon = folium.DivIcon(html=f""" 
            <div>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + PASSED_COLOR + """\" class="bi bi-triangle-fill" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767L7.022 1.566z"/>
                </svg>
            </div>""")

        folium.Marker(
            location=r["coords"],
            tooltip=r["stnames"],
            popup=station_info,
            icon=passed_icon).add_to(station_map)

    # And finally the event itself
    event_info = "MAG: {} LAT: {:.2f} LON: {:.2f} DEPTH: {:.2f}".format(
        event.magnitude, event.latitude, event.longitude, event.depth
    )
    event_icon = folium.DivIcon(html=f""" 
            <div>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" stroke="black" stroke-linecap="square" fill=\"""" + EVENT_COLOR + """\" class="bi bi-star-fill" viewBox="0 0 16 16">
                    <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                </svg>
            </div>""")

    folium.Marker(
        [event.latitude, event.longitude],
        popup=event_info,
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

    # now the static map for the report is created
    # draw map of stations and cities and stuff
    cy = event.latitude
    cx = event.longitude
    xmin = lons.min()
    xmax = lons.max()
    ymin = lats.min()
    ymax = lats.max()

    diff_x = max(abs(cx - xmin), abs(cx - xmax), 1)
    diff_y = max(abs(cy - ymin), abs(cy - ymax), 1)

    xmax = cx + MAP_PADDING * diff_x
    xmin = cx - MAP_PADDING * diff_x
    ymax = cy + MAP_PADDING * diff_y
    ymin = cy - MAP_PADDING * diff_y

    bounds = (xmin, xmax, ymin, ymax)
    figsize = (10, 10)
    cities = Cities.fromDefault()
    mmap = MercatorMap(bounds, figsize, cities)
    mmap.drawCities(draw_dots=True)
    ax = mmap.axes
    draw_scale(ax)
    ax.plot(cx, cy, "r*", markersize=16, transform=mmap.geoproj, zorder=8)

    failed = np.array(
        [
            np.any([trace.hasParameter("failure") for trace in stream])
            for stream in pstreams
        ]
    )

    # Plot the failed first
    ax.scatter(
        lons[failed],
        lats[failed],
        c=FAILED_COLOR,
        marker="v",
        edgecolors="k",
        transform=mmap.geoproj,
        zorder=100,
        s=48,
    )

    # Plot the successes above the failures
    ax.scatter(
        lons[~failed],
        lats[~failed],
        c=PASSED_COLOR,
        marker="^",
        edgecolors="k",
        transform=mmap.geoproj,
        zorder=101,
        s=48,
    )

    passed_marker = mlines.Line2D(
        [],
        [],
        color=PASSED_COLOR,
        marker="^",
        markeredgecolor="k",
        markersize=12,
        label="Passed station",
        linestyle="None",
    )
    failed_marker = mlines.Line2D(
        [],
        [],
        color=FAILED_COLOR,
        marker="v",
        markeredgecolor="k",
        markersize=12,
        label="Failed station",
        linestyle="None",
    )
    earthquake_marker = mlines.Line2D(
        [],
        [],
        color="yellow",
        marker="*",
        markersize=12,
        label="Earthquake Epicenter",
        linestyle="None",
    )
    ax.legend(handles=[passed_marker, failed_marker, earthquake_marker], fontsize=12)

    scale = "50m"
    land = cfeature.NaturalEarthFeature(
        category="physical", name="land", scale=scale, facecolor=LAND_COLOR
    )
    ocean = cfeature.NaturalEarthFeature(
        category="physical", name="ocean", scale=scale, facecolor=OCEAN_COLOR
    )
    ax.add_feature(land)
    ax.add_feature(ocean)
    ax.coastlines(resolution=scale, zorder=10, linewidth=1)
    png_mapfile = os.path.join(event_dir, "stations_map.png")
    plt.savefig(png_mapfile)
    return (png_mapfile, html_mapfile)
