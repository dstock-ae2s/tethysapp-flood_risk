from shapely.geometry import mapping, shape
import fiona
import os
from collections import OrderedDict
from shapely.geometry import MultiPolygon, Point, shape, mapping, LineString, Polygon, MultiLineString
from shapely import wkt
import rasterio
from rasterio.features import shapes
import rasterstats as rs
import numpy as np
from osgeo import gdal
import geopandas as gpd


"""
Function to add a buffer to building outlines resulting in a polygon shapefile
"""
def add_buffer(buffer_val):
    # Set the working directory
    file_name = "Building_Outlines"
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
    os.chdir(SHP_DIR)

    # Reading in the lines shapefile
    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(".shp"):
            line_file = os.path.join(SHP_DIR, file)

    # Read the line shapefile and add a new field 'max_depth'
    with fiona.open(line_file, 'r') as source:

        this_schema = {'properties': OrderedDict([('OBJECTID', 'float:19.11'),
                                                  ('Shape_Leng', 'float:19.11'),
                                                  ('Shape_Area', 'float:19.11'),
                                                  ('Max_Depth', 'float:19.11')]),
                       'geometry': ['Polygon']}
        source_crs = source.crs
        # Set the output file
        file_name = "Bldg_Outline_Polygons"
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        try:
            os.mkdir(SHP_DIR)
        except OSError:
            print("Creation of the directory %s failed" % SHP_DIR)
        else:
            print("Successfully created the directory %s " % SHP_DIR)
        os.chdir(SHP_DIR)
        with fiona.open('Building_Outline_Polygons.shp', 'w', driver='ESRI Shapefile',
                        crs=source_crs, schema=this_schema) as output:
            # Iterate over each line in line file

            for line in source:
                if line['geometry']['type'] == 'LineString':
                    line_shape = shape(line['geometry'])
                    # Add a buffer, creating a polygon
                    line_buffer = line_shape.buffer(float(buffer_val))

                    # Check area to make sure Building Polygon is hollow
                    if line_buffer.area > (line_buffer.length * (float(buffer_val) + 0.001)):
                        line_buffer = line_shape.buffer(0.1)
                        if line_buffer.area > (line_buffer.length * (float(buffer_val) + 0.001)):
                            line_buffer = line_shape.buffer(0.01)
                            if line_buffer.area > (line_buffer.length * (float(buffer_val) + 0.001)):
                                line_buffer = line_shape.buffer(0.001)
                                if line_buffer.area > (line_buffer.length * (float(buffer_val) + 0.001)):
                                    print("Filled polygon")

                    # Save each buffer
                    output.write({'geometry': mapping(line_buffer),
                                  'type': line_buffer.geom_type,
                                  'properties': {'OBJECTID': line['properties']['OBJECTID'],
                                                 'Shape_Leng': line_buffer.length,
                                                 'Shape_Area': line_buffer.area,
                                                 'Max_Depth': 0}})
"""
Function to populate the Max Depth field based on raster data
"""
def max_water_depth(rasters, objectid_name, raster_name):
    # Set the working directory
    file_name = "Bldg_Outline_Polygons"
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/"+file_name+'/'
    os.chdir(SHP_DIR)
    for file in os.listdir(SHP_DIR):
        # Reading the lines shapefile only
        if file.endswith(".shp"):
            f_path = os.path.join(SHP_DIR, file)

    with fiona.open(f_path, 'r') as polygon_file:
        file_name = raster_name
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        os.chdir(SHP_DIR)
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
            raster_stats_dataframe['Max_Depth']=raster_stats_dataframe['max']
            raster_stats_dataframe = raster_stats_dataframe.drop(columns=['mini_raster_array', 'mini_raster_affine', 'mini_raster_nodata', 'max'])

            # raster_stats_dataframe.to_file(filename="Buffered_Depth.shp")
            spatial_join(objectid_name, raster_stats_dataframe)

"""
Function called by max_depth which joins the Max_Depth field to the input buildings shapefile
"""
def spatial_join(objectid_name, raster_stats_dataframe):
    # Set the working directory
    file_name = "Buildings"
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/"+file_name+'/'
    os.chdir(SHP_DIR)

    for file in os.listdir(SHP_DIR):
        # Reading the raster stats shapefile only
        if file.endswith(".shp"):
            building_polygons = os.path.join(SHP_DIR, file)

    """
    for file in os.listdir(SHP_DIR):
        # Reading the raster stats shapefile only
        if file.endswith("Buffered_Depth.shp"):
            f_path = os.path.join(SHP_DIR, file)
        if file.endswith("Buildings.shp"):
            building_polygons = os.path.join(SHP_DIR, file)

    # Read in max depth shapefile, select OBJECTID and Max Depth fields and group by OBJECTID
    depth_file = gpd.read_file(f_path)
    """

    depth_file = raster_stats_dataframe
    selected_cols = ['OBJECTID', 'Max_Depth']
    depth_file = depth_file[selected_cols]
    depth_file = depth_file.rename(columns={'OBJECTID': str(objectid_name)})
    depth_file.fillna(0, inplace=True)
    depth_file_table = depth_file.groupby(str(objectid_name)).agg(
        Max_Depth=('Max_Depth', 'max'))

    # Read in building shapefile and fill null values with 0
    building_file = gpd.read_file(building_polygons)
    building_file.fillna(0, inplace=True)

    # Merge original buildings dataframe with depth table
    buildings_with_depth = building_file.merge(depth_file_table, on=str(objectid_name))

    # Check if the dataframe is empty and if not export to shapefile
    if buildings_with_depth.empty:
        print("Dataframe is empty")
    else:
        # Set the working directory
        file_name = "Buildings_Inundation"
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        try:
            os.mkdir(SHP_DIR)
        except OSError:
            print("Creation of the directory %s failed" % SHP_DIR)
        else:
            print("Successfully created the directory %s " % SHP_DIR)
        os.chdir(SHP_DIR)
        buildings_with_depth.to_file(filename="Building_inundation.shp")
