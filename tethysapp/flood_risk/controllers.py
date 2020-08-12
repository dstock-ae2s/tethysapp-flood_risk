import random
import string
import os

from django.shortcuts import render, reverse
from django import forms
from tethys_sdk.permissions import login_required
from tethys_sdk.gizmos import *
from tethys_sdk.workspaces import user_workspace
from .app import FloodRisk as app
from .ajax_controllers import *
from .utilities import *
import geojson


@login_required()
def home(request):

    context = {}

    return render(request, 'flood_risk/home.html', context)


@login_required()
def building(request):
    """
    Controller for the Flood Risk Layer Generation Page
    """

    form_submitted = False
    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)
    response = geoserver_engine.list_layers(with_properties=False)
    if response['success']:
        for layer in response['result']:
            if layer == 'flood-risk:Streets_Inundation':
                form_submitted = True


    # Define form gizmos

    submit_buildings = Button(
        display_text='Submit',
        name='submit-buildings',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-buildings'},
    )

    map_layers = []
    if form_submitted:
        geoserver_layer = MVLayer(
            source='ImageWMS',
            options={
                'url': 'http://localhost:8080/geoserver/wms',
                'params': {'LAYERS': 'flood-risk:Landuse_Inundation'},
                'serverType': 'geoserver'
            },
            legend_title=""
        )
        map_layers.append(geoserver_layer)

    map_view = MapView(
        height='100%',
        width='100%',
        layers=map_layers,
        controls=[
            'ZoomSlider', 'Rotate', 'FullScreen',
            {'ZoomToExtent': {
                'projection': 'EPSG:4326',
                'extent': [29.25, -4.75, 46.25, 5.2]
            }}
        ],
        basemap=[
            'CartoDB',
            {'CartoDB': {'style': 'dark'}},
            'OpenStreetMap',
            'Stamen',
            'ESRI'
        ],
        view=MVView(
            projection='EPSG:4326',
            center=[37.880859, 0.219726],
            zoom=7,
            maxZoom=18,
            minZoom=2
        )
    )
    context = {
        'submit_buildings': submit_buildings,
        'map_view': map_view,
    }

    return render(request, 'flood_risk/building.html', context)

@login_required()
def street(request):
    """
    Controller for the Street Risk Analysis Page
    """

    form_submitted = False
    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)
    response = geoserver_engine.list_layers(with_properties=False)
    if response['success']:
        for layer in response['result']:
            if layer == 'flood-risk:Streets_Inundation':
                form_submitted = True

    # Define form gizmos
    submit_streets = Button(
        display_text='Submit',
        name='submit-streets',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-streets'},
    )
    distance_input = TextInput(
        display_text='Road Segment Length',
        name='distance-input',
        placeholder=100,
        attributes={'id': 'distance-input'}
    )
    street_buffer = TextInput(
        display_text='Street Buffer',
        name='street-buffer',
        placeholder=0.5,
        attributes={'id': 'street-buffer'}
    )

    map_layers = []
    if form_submitted:
        geoserver_layer = MVLayer(
            source='ImageWMS',
            options={
                'url': 'http://localhost:8080/geoserver/wms',
                'params': {'LAYERS': 'flood-risk:Streets_Inundation'},
                'serverType': 'geoserver'
            },
            legend_title=""
        )
        map_layers.append(geoserver_layer)

    map_view = MapView(
        height='100%',
        width='100%',
        layers=map_layers,
        controls=[
            'ZoomSlider', 'Rotate', 'FullScreen',
            {'ZoomToExtent': {
                'projection': 'EPSG:4326',
                'extent': [29.25, -4.75, 46.25, 5.2]
            }}
        ],
        basemap=[
            'CartoDB',
            {'CartoDB': {'style': 'dark'}},
            'OpenStreetMap',
            'Stamen',
            'ESRI'
        ],
        view=MVView(
            projection='EPSG:4326',
            center=[37.880859, 0.219726],
            zoom=7,
            maxZoom=18,
            minZoom=2
        )
    )
    context = {
        'distance_input':distance_input,
        'street_buffer':street_buffer,
        'submit_streets':submit_streets,
        'map_view':map_view,
    }

    return render(request, 'flood_risk/street.html', context)


@login_required()
def manhole(request):
    """
    Controller for the Manhole page.
    """

    form_submitted = False
    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)
    response = geoserver_engine.list_layers(with_properties=False)
    if response['success']:
        for layer in response['result']:
            if layer == 'flood-risk:MH_Street_Inundation':
                form_submitted = True


    # Define form gizmos
    submit_manhole = Button(
        display_text='Submit',
        name='submit-manhole',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-manhole'},
    )
    manhole_buffer = TextInput(
        display_text='',
        name='manhole-buffer',
        placeholder=50,
        attributes={'id': 'manhole-buffer'},
        classes="input buffer-input",
    )
    map_layers = []
    if form_submitted:

        geoserver_layer = MVLayer(
            source='ImageWMS',
            options={
                'url': 'http://localhost:8080/geoserver/wms',
                'params': {'LAYERS':'flood-risk:MH_Street_Inundation'},
                'serverType': 'geoserver'
            },
            legend_title=""
        )
        map_layers.append(geoserver_layer)


    map_view = MapView(
        height='100%',
        width='100%',
        layers=map_layers,
        controls=[
            'ZoomSlider', 'Rotate', 'FullScreen',
            {'ZoomToExtent':{
                'projection':'EPSG:4326',
                'extent':[29.25, -4.75, 46.25, 5.2]
            }}
        ],
        basemap=[
            'CartoDB',
            {'CartoDB': {'style': 'dark'}},
            'OpenStreetMap',
            'Stamen',
            'ESRI'
        ],
        view=MVView(
            projection='EPSG:4326',
            center=[37.880859, 0.219726],
            zoom=7,
            maxZoom=18,
            minZoom=2
        )
    )
    context = {
        'manhole_buffer':manhole_buffer,
        'submit_manhole':submit_manhole,
        'map_view':map_view,
    }
    return render(request, 'flood_risk/manhole.html', context)

@login_required()
def pipe(request):
    """
    Controller for the Manhole page.
    """

    form_submitted = False
    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)
    response = geoserver_engine.list_layers(with_properties=False)
    if response['success']:
        for layer in response['result']:
            if layer == 'flood-risk:Pipe_Inundation':
                form_submitted = True

    # Define form gizmos
    submit_pipe = Button(
        display_text='Submit',
        name='submit-pipe',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-pipe'},
    )

    map_layers = []
    if form_submitted:

        geoserver_layer = MVLayer(
            source='ImageWMS',
            options={
                'url': 'http://localhost:8080/geoserver/wms',
                'params': {'LAYERS':'flood-risk:Pipe_Inundation'},
                'serverType': 'geoserver'
            },
            legend_title=""
        )
        map_layers.append(geoserver_layer)


    map_view = MapView(
        height='100%',
        width='100%',
        layers=map_layers,
        controls=[
            'ZoomSlider', 'Rotate', 'FullScreen',
            {'ZoomToExtent':{
                'projection':'EPSG:4326',
                'extent':[29.25, -4.75, 46.25, 5.2]
            }}
        ],
        basemap=[
            'CartoDB',
            {'CartoDB': {'style': 'dark'}},
            'OpenStreetMap',
            'Stamen',
            'ESRI'
        ],
        view=MVView(
            projection='EPSG:4326',
            center=[37.880859, 0.219726],
            zoom=7,
            maxZoom=18,
            minZoom=2
        )
    )
    context = {
        'submit_pipe':submit_pipe,
        'map_view':map_view,
    }
    return render(request, 'flood_risk/pipe.html', context)
