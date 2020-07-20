from django.http import JsonResponse, HttpResponse, Http404
from .app import *
import tempfile, shutil
from osgeo import ogr
import os
import json

"""
Function to make a directory if it does not exist and change directories
"""
def mk_change_directory(file_name):
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'

    SHP_DIR = os.path.join(SHP_DIR, '')

    try:
        os.mkdir(SHP_DIR)
    except OSError:
        print("Creation of the directory %s failed" % SHP_DIR)
    else:
        print("Successfully created the directory %s " % SHP_DIR)
    os.chdir(SHP_DIR)


"""
Function to find file of specified file type in directory
"""
def find_file(file_name, ending):
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
    for file in os.listdir(SHP_DIR):
        # Reading the output shapefile only
        if file.endswith(ending):
            file_path = os.path.join(SHP_DIR, file)
            return file_path

"""
Function to move files to user directory and get field names
"""
def move_files_get_fields(shapefile, file_name, filetype):
    SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/'+file_name+'/'

    mk_change_directory(file_name)

    field_list = []
    return_obj = {}

    for f in shapefile:
        f_name = f.name
        f_path = os.path.join(SHP_DIR, f_name)

        with open(f_path, 'wb') as f_local:
            f_local.write(f.read())

    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(filetype):
            f_path = os.path.join(SHP_DIR, file)

            ds = ogr.Open(f_path)
            lyr = ds.GetLayer()

            field_names = [field.name for field in lyr.schema]

            for field in field_names:
                field_list.append(field)

    return_obj["field_names"] = field_list
    return_obj = json.dumps(return_obj)

    return return_obj

"""
Function to move files to user workspace
"""
def move_files(shapefile, file_name):
    SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'

    mk_change_directory(file_name)

    # Iterate over files and add to user workspace
    for f in shapefile:
        f_name = f.name
        f_path = os.path.join(SHP_DIR, f_name)

        with open(f_path, 'wb') as f_local:
            f_local.write(f.read())

    return JsonResponse({"success": "success"})
