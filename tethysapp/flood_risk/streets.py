import fiona
import os
from collections import OrderedDict
from shapely.geometry import MultiPolygon, Point, shape, mapping, LineString, Polygon, MultiLineString
import rasterio
import rasterstats as rs
import numpy as np
import geopandas as gpd

"""
Function to add a buffer to LineStrings resulting in a Polygon shapefile
"""
def add_buffer_generic(streetid, distance, buffer_val, file_name, output_file, output_file2):

    # Split streets at set distance interval
    divide_lines(streetid, distance, file_name, output_file)

    # Edit file to include all fields
    output_file_path = find_file(output_file, (output_file + ".shp"))

    this_output = gpd.read_file(output_file_path)
    this_output.fillna(0, inplace=True)

    input_file_path = find_file(file_name, ".shp")
    this_input = gpd.read_file(input_file_path)
    this_input = this_input.drop(columns=['geometry'])
    this_input.fillna(0, inplace=True)

    streets_with_info = this_output.merge(this_input, on=streetid)

    # Check if the dataframe is empty and if not export to shapefile
    if not streets_with_info.empty:
        mk_change_directory(output_file)
        streets_with_info.to_file(filename=(output_file + ".shp"), overwrite=True)

    buffer_lines(streetid, buffer_val, output_file, output_file2)
    max_water_depth2(streetid, output_file, output_file2, output_file, 'Max_Depth')


"""
Function to divide streets at set distances and output as shapefile
"""
def divide_lines(streetid, distance, file_name, output_file):
    mk_change_directory(file_name)

    # Reading in the lines shapefile
    line_file = find_file(file_name, ".shp")

    # Read the line shapefile and add a new field 'max_depth'
    with fiona.open(line_file, 'r') as source:

        # Set the output file
        this_schema = {'properties': OrderedDict([(streetid, 'float:19.11'),
                                                  ('Index', 'float:19.11'),
                                                  ('Max_Depth', 'float:19.11')]),
                       'geometry': ['LineString']}
        source_crs = source.crs

        # Starting value for new index field
        index = 1

        # Create a directory for the output file
        mk_change_directory(output_file)

        # Output file for total street width
        with fiona.open((output_file + ".shp"), 'w', driver='ESRI Shapefile',
                        crs=source_crs, schema=this_schema) as output:
            # Iterate over each line in line file
            for line in source:
                index = identify_lines(line, output, distance, index, streetid)


"""
Function called by divide_lines to break line down to LineStrings and split lines
"""
def identify_lines(line, output, distance, index, streetid):
    if line['geometry']['type'] == "LineString":
        line_shape = shape(line['geometry'])
        multiline_list = split_line_with_points(line_shape, distance)
        index = iterate_list(multiline_list, output, streetid, line, index)
    elif line['geometry']['type'] == 'MultiLineString':
        line_shape = shape(line['geometry'])
        line_shape_list = list(line_shape)
        for lines in line_shape_list:
            multiline_list = split_line_with_points(lines, distance)
            index = iterate_list(multiline_list, output, streetid, line, index)

    return index


"""
Function called by identify_lines to iterate through a LineString list to output LineStrings
"""
def iterate_list(multiline_list, output, streetid, line, index):
    for oneline in multiline_list:
        if oneline.type == "LineString":
            index = output_linestring(oneline, output, streetid, line, index)
        elif oneline.type == "MultiLineString":
            for singleline in oneline:
                index = output_linestring(singleline, output, streetid, line, index)
    return index


"""
Function which writes a LineString to shapefile
"""
def output_linestring(oneline, output, streetid, line, index):
    output.write({'geometry': mapping(oneline),
                  'type': oneline.geom_type,
                  'properties': {streetid: line['properties'][streetid],
                                 'Index': index,
                                 'Max_Depth': 0}})
    index += 1
    return index


"""
Function to buffer or remove buffer from streets
"""
def buffer_lines(objectid_name, buffer_val, output_file, output_file2):

    mk_change_directory(output_file)

    # Cast OBJECTID field as string
    streetid = str(objectid_name)

    # Reading in the lines shapefile
    line_file = find_file(output_file, ".shp")

    # Read the line shapefile and add a new field 'max_depth'
    with fiona.open(line_file, 'r') as source:

        # Set the output file
        this_schema = {'properties': OrderedDict([(streetid, 'float:19.11'),
                                                  ('Index', 'float:19.11'),
                                                  ('Max_Depth', 'float:19.11')]),
                       'geometry': ['Polygon']}
        source_crs = source.crs

        # Create a directory for the output
        output_file_name = output_file2 + ".shp"
        mk_change_directory(output_file2)

        # Output buffered file
        with fiona.open(output_file_name, 'w', driver='ESRI Shapefile',
                        crs=source_crs, schema=this_schema) as output:
            # Iterate over each line in line file
            index = 1
            for line in source:
                if line['geometry']['type'] == 'LineString':
                    line_shape = shape(line['geometry'])
                    line_buffer = line_shape.buffer(float(buffer_val))
                    index = output_linestring(line_buffer, output, streetid, line, index)
                else:
                    print(line['geometry']['type'])


"""
Function to cut line at specified distance, returning two LineStrings
"""
def cut(line, distance):

    # Check that distance is within line
    if distance <= 0.0 or distance >= line.length:
        return[LineString(line)]

    # Cut line
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

"""
Function to call cut function if sufficient length remaining in line
"""
def split_line_with_points(line, d):
    segments = []
    current_line = line
    d_current = d

    while True:
        if d_current < (line.length):
            seg, current_line = cut(current_line, d)
            segments.append(seg)
            d_current += d
        else:
            segments.append(current_line)
            break

    return segments

"""
Function to populate the Max Depth field based on raster data
"""
def max_water_depth2(objectid, divided_file, output_file2, location, field):
    # Set the working directory
    mk_change_directory(output_file2)
    f_path = find_file(output_file2, (output_file2 + ".shp"))

    with fiona.open(f_path, 'r') as polygon_file:
        mk_change_directory("depth_file")
        rasters = find_file("depth_file", ".tif")

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

            if not raster_stats_dataframe.empty:
                raster_stats_dataframe[field] = raster_stats_dataframe['max']
                raster_stats_dataframe = raster_stats_dataframe.drop(columns=['mini_raster_array', 'mini_raster_affine', 'mini_raster_nodata', 'max', objectid])

                spatial_join2(raster_stats_dataframe, divided_file, location, field)



"""
Function called by max_depth which joins the Max_Depth field to the input streets shapefile
"""
def spatial_join2(raster_stats_dataframe, divided_file, location, field):
    # Set the working directory
    mk_change_directory(location)

    # Read in the streets shapefile
    streets_divided = find_file(location, (divided_file + ".shp"))
    streets_file = gpd.read_file(streets_divided)
    streets_file.fillna(0, inplace=True)
    streets_file = streets_file.drop(columns=[field])

    # Read in the zonal stats dataframe with max depth
    depth_file = raster_stats_dataframe
    depth_file.fillna(0, inplace=True)
    selected_cols = ['Index', field]
    depth_file = depth_file[selected_cols]

    # Merge streets dataframe with depth dataframe
    streets_with_depth = streets_file.merge(depth_file, on='Index')

    # Check if the dataframe is empty and if not export to shapefile
    if not streets_with_depth.empty:
        mk_change_directory("Streets_Inundation")
        streets_with_depth.to_file(filename=("Streets_Inundation.shp"))

"""
Function to make a directory if it does not exist and change directories
"""
def mk_change_directory(file_name):
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
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

