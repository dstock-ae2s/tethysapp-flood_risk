import random
import string
import os

from django.shortcuts import render, reverse
from django import forms
from tethys_sdk.permissions import login_required
from tethys_sdk.gizmos import *
from tethys_sdk.workspaces import user_workspace
from .app import FloodRisk as app
from .field_names import *
from .geoprocessing import *
from .ajax_controllers import *


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    save_button = Button(
        display_text='',
        name='save-button',
        icon='glyphicon glyphicon-floppy-disk',
        style='success',
        attributes={
            'data-toggle':'tooltip',
            'data-placement':'top',
            'title':'Save'
        }
    )

    edit_button = Button(
        display_text='',
        name='edit-button',
        icon='glyphicon glyphicon-edit',
        style='warning',
        attributes={
            'data-toggle':'tooltip',
            'data-placement':'top',
            'title':'Edit'
        }
    )

    remove_button = Button(
        display_text='',
        name='remove-button',
        icon='glyphicon glyphicon-remove',
        style='danger',
        attributes={
            'data-toggle':'tooltip',
            'data-placement':'top',
            'title':'Remove'
        }
    )

    previous_button = Button(
        display_text='Previous',
        name='previous-button',
        attributes={
            'data-toggle':'tooltip',
            'data-placement':'top',
            'title':'Previous'
        }
    )

    next_button = Button(
        display_text='Next',
        name='next-button',
        attributes={
            'data-toggle':'tooltip',
            'data-placement':'top',
            'title':'Next'
        }
    )

    context = {
        'save_button': save_button,
        'edit_button': edit_button,
        'remove_button': remove_button,
        'previous_button': previous_button,
        'next_button': next_button
    }

    return render(request, 'flood_risk/home.html', context)

@login_required()
def layer_gen(request):
    """
    Controller for the Flood Risk Layer Generation Page
    """

    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)
    options = []
    response = geoserver_engine.list_layers(with_properties=False)
    if(response['success']):
        for layer in response['result']:
            options.append((layer.title(), layer))


    # Define form gizmos

    submit_buildings = Button(
        display_text='Submit',
        name='submit-buildings',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-buildings'},
    )
    buffer_input = TextInput(
        display_text='Buffer',
        name='buffer-input',
        placeholder=0,
        attributes={'id':'buffer-input'}
    )
    select_options = SelectInput(
        display_text='Choose Layer',
        name='layer',
        multiple=False,
        options=options,
        attributes={'id': 'geoserver-layers'}
    )
    map_layers = []
    if request.POST and 'layer' in request.POST:
        selected_layer=request.POST['layer']

        geoserver_layer = MVLayer(
            source='ImageWMS',
            options={
                'url': 'http://localhost:8080/geoserver/wms',
                'params': {'LAYERS':selected_layer},
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
        'buffer_input': buffer_input,
        'submit_buildings': submit_buildings,
        'map_view': map_view,
        'select_options': select_options,
    }

    return render(request, 'flood_risk/layer_gen.html', context)

@login_required()
def risk_analysis(request):
    """
    Controller for the Street Risk Analysis Page
    """

    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)
    options = []
    response = geoserver_engine.list_layers(with_properties=False)
    if(response['success']):
        for layer in response['result']:
            options.append((layer.title(), layer))

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
    select_options = SelectInput(
        display_text='Choose Layer',
        name='layer',
        multiple=False,
        options=options,
        attributes={'id': 'geoserver-layers'}
    )
    map_layers = []
    if request.POST and 'layer' in request.POST:
        selected_layer=request.POST['layer']

        geoserver_layer = MVLayer(
            source='ImageWMS',
            options={
                'url': 'http://localhost:8080/geoserver/wms',
                'params': {'LAYERS':selected_layer},
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
        'distance_input':distance_input,
        'street_buffer':street_buffer,
        'submit_streets':submit_streets,
        'map_view':map_view,
        'select_options':select_options,
    }

    return render(request, 'flood_risk/risk_analysis.html', context)


@login_required()
def manhole(request):
    """
    Controller for the Manhole page.
    """

    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)
    options = []
    response = geoserver_engine.list_layers(with_properties=False)
    if(response['success']):
        for layer in response['result']:
            options.append((layer.title(), layer))

    # Define form gizmos
    submit_manhole = Button(
        display_text='Submit',
        name='submit-manhole',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-manhole'},
    )
    manhole_buffer = TextInput(
        display_text='Manhole Buffer',
        name='manhole-buffer',
        placeholder=20,
        attributes={'id': 'manhole-buffer'}
    )
    select_options = SelectInput(
        display_text='Choose Layer',
        name='layer',
        multiple=False,
        options=options,
        attributes={'id': 'geoserver-layers'}
    )
    map_layers = []
    if request.POST and 'layer' in request.POST:
        selected_layer=request.POST['layer']

        geoserver_layer = MVLayer(
            source='ImageWMS',
            options={
                'url': 'http://localhost:8080/geoserver/wms',
                'params': {'LAYERS':selected_layer},
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
        'select_options':select_options,
    }
    return render(request, 'flood_risk/manhole.html', context)
