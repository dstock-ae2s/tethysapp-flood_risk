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
    # Define form gizmos
    
    add_button_raster = Button(
        display_text='Upload Inundation Raster',
        name='add-button',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-depth'},
    )
    add_button_land = Button(
        display_text='Upload Landuse Shapefile',
        name='add-button-land',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-land'},
    )
    add_button_tax = Button(
        display_text='Upload Tax Parcel Shapefile',
        name='add-button-tax',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-tax'},
    )
    process_tax = Button(
        display_text='Perform Tax Analysis',
        name='process-tax',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-process-tax'},
    )
    process_land = Button(
        display_text='Perform Land Use Analysis',
        name='process-land',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-process-land'},
    )
    add_button_shapefile = Button(
        display_text='Upload Building Shapefile',
        name='add-button-shapefile',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-building'},
    )
    buffer_input = TextInput(
        display_text='Buffer',
        name='buffer-input',
        placeholder=0,
        attributes={'id':'buffer-input'}
    )

    context = {
        'add_button_raster':add_button_raster,
        'add_button_land':add_button_land,
        'add_button_tax':add_button_tax,
        'buffer_input':buffer_input,
        'add_button_shapefile':add_button_shapefile,
        'process_tax':process_tax,
        'process_land': process_land
    }

    return render(request, 'flood_risk/layer_gen.html', context)

@login_required()
def risk_analysis(request):
    """
    Controller for the Overall Risk Analysis Page
    """

    # Define form gizmos
    add_button_streets = Button(
        display_text='Upload Street Centerline Shapefile',
        name='add-button-streets',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-streets'},
    )
    distance_input = TextInput(
        display_text='Road Segment Length',
        name='distance-input',
        placeholder=0,
        attributes={'id': 'distance-input'}
    )
    add_button_streetid = Button(
        display_text='Upload Street ID Field',
        name='add-button-streetid',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-streetid'},
    )
    context = {
        'add_button_streets':add_button_streets,
        'distance_input':distance_input,
        'add_button_streetid': add_button_streetid
    }

    return render(request, 'flood_risk/risk_analysis.html', context)
