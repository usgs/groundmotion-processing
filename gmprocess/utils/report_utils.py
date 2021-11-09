#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
import pandas as pd
import folium
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from impactutils.mapping.city import Cities
from impactutils.mapping.mercatormap import MercatorMap
from impactutils.mapping.scalebar import draw_scale
from cartopy import feature as cfeature


OCEAN_COLOR = '#96e8ff'
LAND_COLOR = '#ededaf'
PASSED_COLOR = '#00ac00'
FAILED_COLOR = '#ff2222'
MAP_PADDING = 1.1  # Station map padding value


def draw_stations_map(pstreams, event, event_dir):

    # interactive html map is created first
    lats = np.array([stream[0].stats.coordinates['latitude']
                     for stream in pstreams])
    lons = np.array([stream[0].stats.coordinates['longitude']
                     for stream in pstreams])
    stnames = np.array([stream[0].stats.station
                        for stream in pstreams])
    networks = np.array([stream[0].stats.network
                         for stream in pstreams])

    failed = np.array([
        np.any([trace.hasParameter("failure") for trace in stream])
        for stream in pstreams])

    failure_reasons = list(pd.Series(
        [next(tr for tr in st if tr.hasParameter('failure')).
         getParameter('failure')['reason'] for st in pstreams
         if not st.passed], dtype=str))

    station_map = folium.Map(location=[event.latitude, event.longitude],
                             zoom_start=7, control_scale=True)

    failed_coords = zip(lats[failed], lons[failed])
    failed_stations = stnames[failed]
    failed_networks = networks[failed]
    failed_station_df = pd.DataFrame({
        'stnames': failed_stations,
        'network': failed_networks,
        'coords': failed_coords,
        'reason': failure_reasons
    })

    passed_coords = zip(lats[~failed], lons[~failed])
    passed_stations = stnames[~failed]
    passed_networks = networks[~failed]
    passed_station_df = pd.DataFrame({
        'stnames': passed_stations,
        'network': passed_networks,
        'coords': passed_coords
    })

    # Plot the failed first
    for i, r in failed_station_df.iterrows():
        station_info = 'NET: {} LAT: {:.2f} LON: {:.2f} REASON: {}'.\
            format(r['network'], r['coords'][0], r['coords'][1], r['reason'])
        folium.CircleMarker(
            location=r['coords'],
            tooltip=r['stnames'], popup=station_info,
            color=FAILED_COLOR, fill=True, radius=6).add_to(station_map)

    for i, r in passed_station_df.iterrows():
        station_info = 'NET: {}\n LAT: {:.2f} LON: {:.2f}'.\
            format(r['network'], r['coords'][0], r['coords'][1])
        folium.CircleMarker(
            location=r['coords'], tooltip=r['stnames'], popup=station_info,
            color=PASSED_COLOR, fill=True, radius=10).add_to(station_map)

    event_info = 'MAG: {} LAT: {:.2f} LON: {:.2f} DEPTH: {:.2f}'.\
        format(event.magnitude, event.latitude, event.longitude, event.depth)
    folium.CircleMarker(
        [event.latitude, event.longitude], popup=event_info,
        color='yellow', fill=True, radius=15).add_to(station_map)

    html_mapfile = os.path.join(event_dir, 'stations_map.html')
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
    ax.plot(cx, cy, 'r*', markersize=16,
            transform=mmap.geoproj, zorder=8)

    failed = np.array([
        np.any([trace.hasParameter("failure") for trace in stream])
        for stream in pstreams])

    # Plot the failed first
    ax.scatter(lons[failed], lats[failed], c=FAILED_COLOR,
               marker='v', edgecolors='k', transform=mmap.geoproj, zorder=100,
               s=48)

    # Plot the successes above the failures
    ax.scatter(lons[~failed], lats[~failed], c=PASSED_COLOR,
               marker='^', edgecolors='k', transform=mmap.geoproj, zorder=101,
               s=48)

    passed_marker = mlines.Line2D(
        [], [], color=PASSED_COLOR, marker='^',
        markeredgecolor='k', markersize=12,
        label='Passed station', linestyle='None')
    failed_marker = mlines.Line2D(
        [], [], color=FAILED_COLOR, marker='v',
        markeredgecolor='k', markersize=12,
        label='Failed station', linestyle='None')
    earthquake_marker = mlines.Line2D(
        [], [], color='red', marker='*',
        markersize=12,
        label='Earthquake Epicenter',
        linestyle='None')
    ax.legend(handles=[passed_marker, failed_marker, earthquake_marker],
              fontsize=12)

    scale = '50m'
    land = cfeature.NaturalEarthFeature(
        category='physical',
        name='land',
        scale=scale,
        facecolor=LAND_COLOR)
    ocean = cfeature.NaturalEarthFeature(
        category='physical',
        name='ocean',
        scale=scale,
        facecolor=OCEAN_COLOR)
    ax.add_feature(land)
    ax.add_feature(ocean)
    ax.coastlines(resolution=scale, zorder=10, linewidth=1)
    png_mapfile = os.path.join(event_dir, 'stations_map.png')
    plt.savefig(png_mapfile)
    return (png_mapfile, html_mapfile)
