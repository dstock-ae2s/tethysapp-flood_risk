import fiona
import os
from collections import OrderedDict
from shapely.geometry import MultiPolygon, Point, shape, mapping, LineString, Polygon, MultiLineString
import rasterio
import rasterstats as rs
import numpy as np
import geopandas as gpd
from geopandas.tools import sjoin

"""
Function to add a buffer to building outlines resulting in a polygon shapefile
"""
def add_buffer_generic(objectid_name, distance, buffer_val, file_name, output_file, output_file2):
    streetid = str(objectid_name)

    divide_lines(streetid, distance, float(buffer_val), file_name, output_file)

    # Edit file to include all fields
    output_file_name = output_file + ".shp"
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + output_file + '/'
    for file in os.listdir(SHP_DIR):
        # Reading the output shapefile only
        if file.endswith(output_file_name):
            output_file_path = os.path.join(SHP_DIR, file)
    this_output = gpd.read_file(output_file_path)
    this_output.fillna(0, inplace=True)

    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
    for file in os.listdir(SHP_DIR):
        # Reading the output shapefile only
        if file.endswith(".shp"):
            input_file_path = os.path.join(SHP_DIR, file)
    this_input = gpd.read_file(input_file_path)
    this_input = this_input.drop(columns=['geometry'])
    this_input.fillna(0, inplace=True)

    streets_with_info = this_output.merge(this_input, on=streetid)

    # Check if the dataframe is empty and if not export to shapefile
    if streets_with_info.empty:
        print("Dataframe is empty")
    else:
        # Set the working directory
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + output_file + '/'
        os.chdir(SHP_DIR)
        # Clear existing files

        for file in os.listdir(SHP_DIR):
            os.remove(file)
        file_name = output_file + ".shp"
        streets_with_info.to_file(filename=file_name, overwrite=True)

    divided_file = output_file
    buffer_lines(objectid_name, buffer_val, output_file, output_file2, 'Max_Depth')
    max_water_depth2(objectid_name, buffer_val, divided_file, output_file2, output_file, 'Max_Depth')

    """
    buffer_val = 1
    output_file2 = "Streets_CL"
    divided_file = "Max_Depth"
    buffer_lines(objectid_name, buffer_val, output_file, output_file2, 'Depth_CL')
    max_water_depth2(objectid_name, buffer_val, divided_file, output_file2, 'Streets_Inundation', 'Depth_CL')
    """

def divide_lines(streetid, distance, buffer_val, file_name, output_file):

    # Set the working directory
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
    os.chdir(SHP_DIR)

    output_file_name = output_file + ".shp"

    # Reading in the lines shapefile
    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(".shp"):
            line_file = os.path.join(SHP_DIR, file)

    # Read the line shapefile and add a new field 'max_depth'
    with fiona.open(line_file, 'r') as source:

        this_schema = {'properties': OrderedDict([(streetid, 'float:19.11'),
                                                  ('Max_Depth', 'float:19.11'),
                                                  ('Depth_CL', 'float:19.11')]),
                       'geometry': ['LineString']}
        source_crs = source.crs
        # Set the output file
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + output_file + '/'
        try:
            os.mkdir(SHP_DIR)
        except OSError:
            print("Creation of the directory %s failed" % SHP_DIR)
        else:
            print("Successfully created the directory %s " % SHP_DIR)
        os.chdir(SHP_DIR)
        # Output file for total street width
        with fiona.open(output_file_name, 'w', driver='ESRI Shapefile',
                        crs=source_crs, schema=this_schema) as output:
            # Iterate over each line in line file
            for line in source:
                if line['geometry']['type'] == 'LineString':
                    line_shape = shape(line['geometry'])

                    # Split the LineString at the points list
                    multiline_list = split_line_with_points(line_shape, distance, buffer_val)

                    for oneline in multiline_list:
                        if oneline.type == "LineString":
                            output.write({'geometry': mapping(oneline),
                                          'type': oneline.geom_type,
                                          'properties': {streetid: line['properties'][streetid],
                                                         'Max_Depth': 0,
                                                         'Depth_CL': 0}})
                        elif oneline.type == "MultiLineString":
                            for multiline in oneline:
                                output.write({'geometry': mapping(multiline),
                                              'type': multiline.geom_type,
                                              'properties': {streetid: line['properties'][streetid],
                                                             'Max_Depth': 0,
                                                             'Depth_CL': 0}})
                elif line['geometry']['type'] == 'MultiLineString':
                    line_shape = shape(line['geometry'])

                    line_shape_list = list(line_shape)
                    for lines in line_shape_list:

                        # Split the LineString at the points list

                        multiline_list = split_line_with_points(lines, distance, buffer_val)

                        for oneline in multiline_list:
                            if oneline.type == "LineString":
                                output.write({'geometry': mapping(oneline),
                                              'type': oneline.geom_type,
                                              'properties': {streetid: line['properties'][streetid],
                                                             'Max_Depth': 0,
                                                             'Depth_CL': 0}})
                            elif oneline.type == "MultiLineString":
                                for multiline in oneline:
                                    output.write({'geometry': mapping(multiline),
                                                  'type': multiline.geom_type,
                                                  'properties': {streetid: line['properties'][streetid],
                                                                 'Max_Depth': 0,
                                                                 'Depth_CL': 0}})


def buffer_lines(objectid_name, buffer_val, output_file, output_file2, field):

    # Set the working directory
    file_name = output_file
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
    os.chdir(SHP_DIR)

    streetid = str(objectid_name)

    # Reading in the lines shapefile
    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(".shp"):
            line_file = os.path.join(SHP_DIR, file)

    # Read the line shapefile and add a new field 'max_depth'
    with fiona.open(line_file, 'r') as source:

        this_schema = {'properties': OrderedDict([(streetid, 'float:19.11'),
                                                  (field, 'float:19.11')]),
                       'geometry': ['Polygon']}
        if float(buffer_val)<0:
            this_schema = {'properties': OrderedDict([(field, 'float:19.11')]),
                           'geometry': ['Polygon']}
        source_crs = source.crs
        # Set the output file
        file_name = output_file2
        output_file_name = output_file2 + ".shp"
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        try:
            os.mkdir(SHP_DIR)
        except OSError:
            print("Creation of the directory %s failed" % SHP_DIR)
        else:
            print("Successfully created the directory %s " % SHP_DIR)
        os.chdir(SHP_DIR)
        # Output file for total street width
        with fiona.open(output_file_name, 'w', driver='ESRI Shapefile',
                        crs=source_crs, schema=this_schema) as output:
            # Iterate over each line in line file
            for line in source:
                if line['geometry']['type'] == 'LineString':
                    line_shape = shape(line['geometry'])
                    line_buffer = line_shape.buffer(float(buffer_val))
                    output.write({'geometry': mapping(line_buffer),
                                  'type': line_buffer.geom_type,
                                  'properties': {streetid: line['properties'][streetid],
                                                 field: 0}})
                elif float(buffer_val)<0 and line['geometry']['type'] == 'Polygon':
                    line_shape = shape(line['geometry'])
                    line_buffer = line_shape.buffer(float(buffer_val))
                    output.write({'geometry': mapping(line_buffer),
                                  'type': line_buffer.geom_type,
                                  'properties': {field: line['properties'][field]}})
                else:
                    print(line['geometry']['type'])


def cut(line, distance):
    if distance <= 0.0 or distance >= line.length:
        return[LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]

def split_line_with_points(line, d, buffer_val):
    segments = []
    current_line = line

    d_current = d
    if d_current < (line.length-buffer_val):
        seg, current_line = cut(current_line, d)
        segments.append(seg)
    else:
        segments.append(line)

    while d_current < line.length:
        d_current += d
        if (d_current < line.length-buffer_val):
            seg, current_line = cut(current_line, d)
            segments.append(seg)
        else:
            segments.append(current_line)

    return segments

"""
Function to populate the Max Depth field based on raster data
"""

def max_water_depth2(objectid, buffer_val, divided_file, output_file2, location, field):
    # Set the working directory
    file_name = output_file2
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/"+file_name+'/'
    os.chdir(SHP_DIR)
    output_file_name = output_file2 + ".shp"
    for file in os.listdir(SHP_DIR):
        # Reading the polygon shapefiles only
        if file.endswith(output_file_name):
            f_path = os.path.join(SHP_DIR, file)

    with fiona.open(f_path, 'r') as polygon_file:
        file_name = "Inundation_Raster"
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        os.chdir(SHP_DIR)
        for file in os.listdir(SHP_DIR):
            # Reading the raster only
            if file.endswith(".tif"):
                rasters = os.path.join(SHP_DIR, file)
        with rasterio.open(rasters) as raster_file:

            transform = raster_file.transform
            transform.to_gdal()
            array = raster_file.read(1)
            array[array==0] = np.nan

            # Extract zonal stats
            raster_stats = rs.zonal_stats(polygon_file,
                                          array,
                                          all_touched=True,
                                          nodata=raster_file.nodata,
                                          affine=transform,
                                          geojson_out=True,
                                          raster_out=True,
                                          copy_properties=True,
                                          stats='max')

            # Add max depth to max depth field and export raster stats to a shapefile
            raster_stats_dataframe = gpd.GeoDataFrame.from_features(raster_stats)
            print(field)
            print(raster_stats_dataframe.head())
            print(raster_stats_dataframe.dtypes)
            print(raster_stats_dataframe.shape)
            if not raster_stats_dataframe.empty:
                raster_stats_dataframe[field] = raster_stats_dataframe['max']

                raster_stats_dataframe = raster_stats_dataframe.drop(columns=['mini_raster_array', 'mini_raster_affine', 'mini_raster_nodata', 'max', objectid])

                file_name = "Street_Depth"
                if raster_stats_dataframe.empty:
                    print("Dataframe is empty")
                else:
                    # Set the working directory
                    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
                    try:
                        os.mkdir(SHP_DIR)
                    except OSError:
                        print("Creation of the directory %s failed" % SHP_DIR)
                    else:
                        print("Successfully created the directory %s " % SHP_DIR)
                    os.chdir(SHP_DIR)
                    raster_stats_dataframe.to_file(filename="Street_Depth.shp")

                buffer_val = (float(buffer_val)-1)*(-1)
                buffer_lines(objectid, buffer_val, file_name, "Streets_unbuffered", field)

                spatial_join2("Streets_unbuffered", divided_file, location, field)



"""
Function called by max_depth which joins the Max_Depth field to the input buildings shapefile
"""

def spatial_join2(streets_unbuffered, divided_file, location, field):
    # Set the working directory
    file_name = location
    input_file_name = divided_file + ".shp"
    output_file_name = field+".shp"
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/"+file_name+'/'
    os.chdir(SHP_DIR)

    for file in os.listdir(SHP_DIR):
        # Reading the streets cl shapefile only
        if file.endswith(input_file_name):
            streets_divided = os.path.join(SHP_DIR, file)

    file_name = streets_unbuffered
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
    os.chdir(SHP_DIR)

    for file in os.listdir(SHP_DIR):
        # Reading the streets cl shapefile only
        if file.endswith(".shp"):
            depth_file = os.path.join(SHP_DIR, file)

    depth_file = gpd.read_file(depth_file)
    depth_file.fillna(0, inplace=True)

    # Read in building shapefile and fill null values with 0
    streets_file = gpd.read_file(streets_divided)
    #streets_file = streets_file.drop(columns=[field, objectid])
    streets_file.fillna(0, inplace=True)

    # Merge original buildings dataframe with depth table

    streets_file = streets_file.drop(columns=[field])

    print("DROPPED COLS DEPTH")
    print(depth_file.head())
    print(depth_file.dtypes)
    print(depth_file.shape)
    print("DROPPED COLS STREETS")
    print(streets_file.head())
    print(streets_file.dtypes)
    print(streets_file.shape)

    join_file = depth_file
    target_file = streets_file
    streets_with_depth = sjoin(join_file, target_file, how='right', op='contains')
    streets_with_depth = streets_with_depth.dissolve(by='index_left', aggfunc='first')

    print("MERGE")
    print(streets_with_depth.head())
    print(streets_with_depth.dtypes)
    print(streets_with_depth.shape)

    # Check if the dataframe is empty and if not export to shapefile
    if streets_with_depth.empty:
        print("Dataframe is empty")
    else:
        # Set the working directory
        file_name = "Streets_Inundation"
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        try:
            os.mkdir(SHP_DIR)
        except OSError:
            print("Creation of the directory %s failed" % SHP_DIR)
        else:
            print("Successfully created the directory %s " % SHP_DIR)
        os.chdir(SHP_DIR)
        streets_with_depth.to_file(filename=output_file_name)
