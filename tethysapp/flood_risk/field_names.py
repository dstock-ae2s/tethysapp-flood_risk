from django.http import JsonResponse, HttpResponse, Http404
from osgeo import ogr
from .app import *
import tempfile, shutil
import os
import json

def get_field_names(shapefile, file_extension, file_name):
    SHP_DIR = '/home/dstock/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/'+file_name+'/'
    SHP_DIR = os.path.join(SHP_DIR, '')
    field_list = []
    return_obj = {}
    for f in shapefile:
        f_name = f.name
        f_path = os.path.join(SHP_DIR, f_name)
        
        with open(f_path, 'wb') as f_local:
            f_local.write(f.read())
            
    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(file_extension):
            f_path = os.path.join(SHP_DIR, file)

            ds = ogr.Open(f_path)
            lyr = ds.GetLayer()
            
            field_names = [field.name for field in lyr.schema]
            
            for field in field_names:
                field_list.append(field)
                
    return_obj["field_names"]= field_list
    return_obj = json.dumps(return_obj)
    
    return return_obj


def get_field_names_singular(file_extension, file_name):
    SHP_DIR = '/home/dstock/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'
    SHP_DIR = os.path.join(SHP_DIR, '')
    field_list = []
    return_obj = {}

    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(file_extension):
            f_path = os.path.join(SHP_DIR, file)

            ds = ogr.Open(f_path)
            lyr = ds.GetLayer()

            field_names = [field.name for field in lyr.schema]

            for field in field_names:
                field_list.append(field)

    return_obj["field_names"] = field_list
    return_obj = json.dumps(return_obj)

    return return_obj
