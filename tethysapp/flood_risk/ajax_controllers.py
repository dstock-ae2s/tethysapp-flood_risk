from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from tethys_sdk.permissions import login_required
from tethys_sdk.gizmos import ToggleSwitch
import json, time
import os
from .app import *
from tethys_sdk.gizmos import *
import requests
from .move_files import *
from .geoprocessing import *
from .max_depth import *
from .field_names import *
from .tax_parcel import *
from .landuse import *
from .streets import *

"""
Ajax controller which imports building shapefiles to the user workspace
"""
def building_process(request):
    print("Correct App")
    return_obj = {}
    file_name = "Buildings"
    SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/'+file_name+'/'
    try:
        os.mkdir(SHP_DIR)
    except OSError:
        print("Creation of the directory %s failed" % SHP_DIR)
    else:
        print("Successfully created the directory %s " % SHP_DIR)

    if request.is_ajax() and request.method == 'POST':

        # Add building shapefiles to user directory
        # info = request.POST

        bldg_shapefile = request.FILES.getlist('shapefile')
        
        field_names = get_field_names(bldg_shapefile, ".shp", file_name)
        field_names = json.loads(field_names)

        return_obj["field_names"] = field_names["field_names"]

        buffer_val = request.POST["buffer"]
        if buffer_val=="":
            buffer_val = 1

        # Output building boundaries from building polygons shapefile
        for file in os.listdir(SHP_DIR):
            # Reading the shapefile only
            if file.endswith(".shp"):
                f_path = os.path.join(SHP_DIR, file)
                polygon_to_line(f_path, file_name)
                add_buffer(buffer_val)

        return JsonResponse(return_obj)

"""
Ajax controller which imports flood depth raster
"""
def raster_process(request):
    response = {}

    if request.is_ajax() and request.method == 'POST':
        info = request.POST

        raster = request.FILES.getlist('raster')

        # Move file to user workspace
        file_name = "Inundation_Raster"
        sub_initial(raster, ".tif", file_name)

        # Get OBJECTID field name
        objectid_name = request.POST["objectid_field"]

        # Add max depth from raster to building boundary lines
        file_name = "Building_Outlines"
        SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'
        for file in os.listdir(SHP_DIR):
            # Reading the shapefile only
            if file.endswith(".shp"):
                f_path = os.path.join(SHP_DIR, file)
        file_name = "Inundation_Raster"
        SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'
        for file in os.listdir(SHP_DIR):
            # Reading the raster only
            if file.endswith(".tif"):
                r_path = os.path.join(SHP_DIR, file)
                max_water_depth(r_path, objectid_name, file_name)

        response = {"success":"success"}

        return JsonResponse(response)

"""
Ajax controller which imports tax parcels shapefile
"""
def tax_process(request):
    print("In the tax process ajax")
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':
        print("In the ajax if statement")
        # info = request.POST

        tax_shapefile = request.FILES.getlist('shapefile')

        file_name = "Tax_Parcel"

        # Move file to user workspace
        sub_initial(tax_shapefile, ".shp", file_name)

        print("After sub initial")

        SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'
        SHP_DIR = os.path.join(SHP_DIR, '')
        for file in os.listdir(SHP_DIR):
            # Checking if the shapefile is in the directory
            if file.endswith(".shp"):
                tax_names = get_field_names_singular(".shp", file_name)
                tax_names = json.loads(tax_names)
                return_obj["tax_names"] = tax_names["field_names"]

        if not return_obj:
            return_obj = {"success": "success"}

        return JsonResponse(return_obj)


"""
Ajax controller which extracts tax parcel value and appends to Building Inundation shapefile
"""
def tax_process2(request):
    response = {}

    if request.is_ajax() and request.method == 'POST':
        # info = request.POST

        # Get tax field name
        tax_name = request.POST["tax_field"]
        taxid_name = request.POST["taxid_field"]
        # Get OBJECTID field name

        file_name = "Tax_Parcel"
        SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'
        for file in os.listdir(SHP_DIR):
            # Reading the shapefile only
            if file.endswith(".shp"):
                f_path = os.path.join(SHP_DIR, file)
                tax_join('OBJECTID', taxid_name, tax_name, f_path)

        response = {"success": "success"}

        return JsonResponse(response)


"""
Ajax controller which imports land use shapefile
"""
def land_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        # info = request.POST

        land_shapefile = request.FILES.getlist('shapefile')

        file_name = "Landuse"

        # Move file to user workspace
        sub_initial(land_shapefile, ".shp", file_name)

        SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'
        SHP_DIR = os.path.join(SHP_DIR, '')
        for file in os.listdir(SHP_DIR):
            # Checking if the shapefile is in the directory
            if file.endswith(".shp"):
                land_names = get_field_names_singular(".shp", file_name)
                land_names = json.loads(land_names)

                return_obj["land_names"] = land_names["field_names"]

        if not return_obj:
            return_obj = {"success": "success"}

        return JsonResponse(return_obj)

"""
Ajax controller which extracts land use and appends to Building Inundation shapefile
"""
def land_process2(request):
    response = {}

    if request.is_ajax() and request.method == 'POST':
        # info = request.POST

        # Get land use field name
        land_name = request.POST["land_field"]
        landid_name = request.POST["landid_field"]
        # Get OBJECTID field name

        file_name = "Landuse"
        SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'
        for file in os.listdir(SHP_DIR):
            # Reading the shapefile only
            if file.endswith(".shp"):
                f_path = os.path.join(SHP_DIR, file)
                land_join('OBJECTID', landid_name, land_name, f_path)

        response = {"success": "success"}

        return JsonResponse(response)


"""
Ajax controller which imports streets shapefiles to the user workspace
"""


def streets_process(request):
    return_obj = {}
    file_name = "Streets"
    SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'
    try:
        os.mkdir(SHP_DIR)
    except OSError:
        print("Creation of the directory %s failed" % SHP_DIR)
    else:
        print("Successfully created the directory %s " % SHP_DIR)

    if request.is_ajax() and request.method == 'POST':

        # Add building shapefiles to user directory
        # info = request.POST

        streets_shapefile = request.FILES.getlist('shapefile')
        # Move file to user workspace
        sub_initial(streets_shapefile, ".shp", file_name)

        for file in os.listdir(SHP_DIR):
            # Checking if the shapefile is in the directory
            if file.endswith(".shp"):
                streetid_names = get_field_names_singular(".shp", file_name)
                streetid_names = json.loads(streetid_names)

                return_obj["streetid_names"] = streetid_names["field_names"]

        return JsonResponse(return_obj)

def streets_process2(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':
        file_name = "Streets"

        streetid = request.POST["streetid_field"]

        output_file = "Streets_divided"
        output_file2 = "Streets_buffered"

        buffer_val = request.POST["buffer"]
        if buffer_val == "":
            buffer_val = 20
        distance_val = request.POST["distance"]

        add_buffer_generic(streetid, float(distance_val), buffer_val, file_name, output_file, output_file2)

        #max_water_depth2(output_file, output_file2, 'Max_Depth')

        return JsonResponse(return_obj)

