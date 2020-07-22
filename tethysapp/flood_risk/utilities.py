from django.http import JsonResponse, HttpResponse, Http404
import fiona
import os
from shapely.geometry import MultiPolygon, Point, shape, mapping, LineString, Polygon, MultiLineString
from .utilities import *
from osgeo import ogr, osr
from pyproj.crs import CRS
import json
from .app import FloodRisk as app
from collections import OrderedDict

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

"""
Function to move files to geoserver
"""
def move_geoserver(file_name):
    GEOSERVER_URI = 'http://www.example.com/flood-risk'
    WORKSPACE = 'flood-risk'

    # Retrieve a geoserver engine
    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine = True)

    # Check for workspace and create workspace for app if it doesn't exist
    response = geoserver_engine.list_workspaces()

    SHP_DIR = '/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/' + file_name + '/'

    file_base = SHP_DIR+file_name

    mk_change_directory(file_name)

    if response['success']:
        workspaces = response['result']

        if WORKSPACE not in workspaces:
            geoserver_engine.create_workspace(workspace_id=WORKSPACE, uri=GEOSERVER_URI)

    # Upload shapefile to GeoServer
    store = ''.join(file_name)
    store_id = WORKSPACE +':' + store
    geoserver_engine.create_shapefile_resource(
        store_id=store_id,
        shapefile_base=file_base,
        overwrite=True
    )

"""
Function to buffer
"""
def simple_buffer(objectid_name, buffer_val, first_file, second_file, output_geometry, geom_to_buffer):

    mk_change_directory(first_file)

    # Cast OBJECTID field as string
    objectid = str(objectid_name)

    # Reading in the lines shapefile
    input_file = find_file(first_file, ".shp")

    # Reading in the crs and converting
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(input_file)
    layer = dataset.GetLayer()
    spatialRef = layer.GetSpatialRef()
    dc_crs = CRS.from_wkt(spatialRef.ExportToWkt())
    fio_crs = dc_crs.to_wkt()

    # Read the line shapefile and add a new field 'max_depth'
    with fiona.open(input_file, 'r') as source:

        # Set the output file
        this_schema = {'properties': OrderedDict([(objectid, 'float:19.11'),
                                                  ('Index', 'float:19.11'),
                                                  ('Max_Depth', 'float:19.11')]),
                       'geometry': [output_geometry]}
        source_crs = fio_crs

        # Create a directory for the output
        output_file_name = second_file + ".shp"
        mk_change_directory(second_file)

        # Output buffered file
        with fiona.open(output_file_name, 'w', driver='ESRI Shapefile',
                        crs=source_crs, schema=this_schema) as output:
            # Iterate over each line in line file
            index = 1
            for item in source:
                if item['geometry']['type'] == geom_to_buffer:
                    item_shape = shape(item['geometry'])
                    item_buffer = item_shape.buffer(float(buffer_val))
                    index = output_shape(item_buffer, output, objectid, item, index)
                else:
                    print(item['geometry']['type'])

"""
Function which writes to shapefile
"""
def output_shape(oneline, output, objectid, line, index):
    output.write({'geometry': mapping(oneline),
                  'type': oneline.geom_type,
                  'properties': {objectid: line['properties'][objectid],
                                 'Index': index,
                                 'Max_Depth': 0}})
    index += 1
    return index

