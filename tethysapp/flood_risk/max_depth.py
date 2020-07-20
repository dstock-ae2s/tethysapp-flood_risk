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
from .utilities import *


"""
Function to add a buffer to building outlines resulting in a polygon shapefile
"""
def add_buffer(buffer_val, id_field):
    not_empty_file = True

    # Set the working directory
    mk_change_directory("Building_Outlines")
    line_file = find_file("Building_Outlines", ".shp")

    # Read the line shapefile and add a new field 'max_depth'
    with fiona.open(line_file, 'r') as source:

        this_schema = {'properties': OrderedDict([(id_field, 'float:19.11'),
                                                  ('Shape_Leng', 'float:19.11'),
                                                  ('Shape_Area', 'float:19.11'),
                                                  ('Max_Depth', 'float:19.11')]),
                       'geometry': ['Polygon']}
        source_crs = source.crs
        # Set the output file
        mk_change_directory("Bldg_Outline_Polygons")
        output_path = find_file("Bldg_Outline_Polygons", ".shp")
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
                                  'properties': {id_field: line['properties'][id_field],
                                                 'Shape_Leng': line_buffer.length,
                                                 'Shape_Area': line_buffer.area,
                                                 'Max_Depth': 0}})

            if not os.stat(output_path).st_size == 0:
                not_empty_file = False
    return not_empty_file
"""
Function to populate the Max Depth field based on raster data
"""
def max_water_depth(rasters, objectid_name, raster_name):
    not_empty_file = True

    # Set the working directory
    f_path = find_file("Bldg_Outline_Polygons", ".shp")
    mk_change_directory("Bldg_Outline_Polygons")

    with fiona.open(f_path, 'r') as polygon_file:
        mk_change_directory(raster_name)
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
                raster_stats_dataframe['Max_Depth']=raster_stats_dataframe['max']
                raster_stats_dataframe = raster_stats_dataframe.drop(columns=['mini_raster_array', 'mini_raster_affine', 'mini_raster_nodata', 'max'])

                # raster_stats_dataframe.to_file(filename="Buffered_Depth.shp")
                spatial_join(objectid_name, raster_stats_dataframe)

                output_path = find_file("Buildings_Inundation", ".shp")
                if not os.stat(output_path).st_size == 0:
                    not_empty_file = False
    return not_empty_file

"""
Function called by max_depth which joins the Max_Depth field to the input buildings shapefile
"""
def spatial_join(objectid_name, raster_stats_dataframe):
    # Set the working directory

    mk_change_directory("bldg_file")
    building_polygons = find_file("bldg_file", ".shp")

    depth_file = raster_stats_dataframe
    selected_cols = [objectid_name, 'Max_Depth']
    depth_file = depth_file[selected_cols]
    # depth_file = depth_file.rename(columns={'OBJECTID': str(objectid_name)})
    depth_file.fillna(0, inplace=True)

    depth_file_table = depth_file.groupby(str(objectid_name)).agg(
        Max_Depth=('Max_Depth', 'max'))

    # Read in building shapefile and fill null values with 0
    building_file = gpd.read_file(building_polygons)
    building_file.fillna(0, inplace=True)

    # Merge original buildings dataframe with depth table
    buildings_with_depth = building_file.merge(depth_file_table, on=str(objectid_name))

    # Check if the dataframe is empty and if not export to shapefile
    if not buildings_with_depth.empty:
        mk_change_directory("Buildings_Inundation")
        buildings_with_depth.to_file(filename="Building_inundation.shp")
