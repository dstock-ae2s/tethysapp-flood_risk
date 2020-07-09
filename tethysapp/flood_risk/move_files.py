import sys
import os.path
import subprocess
from .app import *
from django.http import JsonResponse, HttpResponse, Http404
import tempfile, shutil
from .geojson import *
import json

"""
Function to move files to user workspace
"""
def sub_initial(shapefile, file_extension, file_name):
    print("In the sub initial function")
    # Set temporary directory
    SHP_DIR = '/home/dstock/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/'+file_name+'/'
    try:
        os.mkdir(SHP_DIR)
    except OSError:
        print("Creation of the directory %s failed" % SHP_DIR)
    else:
        print("Successfully created the directory %s " % SHP_DIR)

    SHP_DIR = os.path.join(SHP_DIR, '')

    temp_dir = tempfile.mkdtemp()
    # Iterate over files and add to user workspace
    for f in shapefile:
        f_name = f.name
        f_path = os.path.join(SHP_DIR, f_name)

        with open(f_path, 'wb') as f_local:
            f_local.write(f.read())

    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(file_extension):
            f_path = os.path.join(SHP_DIR, file)
            pol_shp = f_path
            pol_name = os.path.splitext(f_name)[0]

    return JsonResponse({"success": "success"})
