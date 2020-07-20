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

    context = {
        'buffer_input': buffer_input,
        'submit_buildings': submit_buildings,
    }

    return render(request, 'flood_risk/layer_gen.html', context)

@login_required()
def risk_analysis(request):
    """
    Controller for the Overall Risk Analysis Page
    """

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
    context = {
        'distance_input':distance_input,
        'street_buffer':street_buffer,
        'submit_streets':submit_streets,
    }

    return render(request, 'flood_risk/risk_analysis.html', context)
