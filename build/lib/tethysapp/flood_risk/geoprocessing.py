import shapely
from shapely.geometry import MultiPolygon, Point, shape, mapping, LineString, Polygon
import geopandas as gpd
import fiona
import tempfile, shutil
from collections import OrderedDict
import os
from .max_depth import *

"""
Convert polygon shapefile to lines shapefile
"""
def polygon_to_line(shapefile, file_name):

    # Set the working directory
    SHP_DIR = "/home/dstock/trial/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/"+file_name+'/'
    os.chdir(SHP_DIR)

    # Open the Buildings shapefile
    with fiona.open(shapefile) as source:
        this_schema = {'properties': OrderedDict([('OBJECTID', 'float:19.11'),
                                                  ('Shape_Leng', 'float:19.11'),
                                                  ('Shape_Area', 'float:19.11'),
                                                  ('Max_Depth', 'float:19.11')]),
                       'geometry': ['LineString']}
        # Create a file to save the lines shapefile
        file_name = "Building_Outlines"
        SHP_DIR = "/home/dstock/trial/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        try:
            os.mkdir(SHP_DIR)
        except OSError:
            print("Creation of the directory %s failed" % SHP_DIR)
        else:
            print("Successfully created the directory %s " % SHP_DIR)
        os.chdir(SHP_DIR)
        with fiona.open('Building_Outlines.shp', 'w', driver='ESRI Shapefile',
                        crs=source.crs, schema=this_schema) as output:
            # Iterate over the Polygons and MultiPolygons in the buildings shapefile
            for polys in source:
                if polys['geometry']['type'] == 'MultiPolygon':
                    multipolygon = shape(polys['geometry'])
                    polygon_list = list(multipolygon)
                    # Iterate over the Polygons in each MultiPolygon
                    for pol in polygon_list:
                        # Identify the boundary of each Polygon
                        boundary = pol.boundary
                        if boundary.type == 'MultiLineString':
                            # Iterate over the LineStrings in each MultiLineString
                            for line in boundary:
                                # Save each LineString to the lines shapefile
                                output.write({'geometry': mapping(line),
                                              'type': line.geom_type,
                                              'properties': {'OBJECTID': polys['properties']['OBJECTID'],
                                                             'Shape_Leng': line.length,
                                                             'Shape_Area': line.area,
                                                             'Max_Depth': 0}})
                        elif boundary.type == 'LineString':
                            # Save each LineString to the lines shapefile
                            output.write({'geometry': mapping(boundary),
                                          'type': boundary.geom_type,
                                          'properties': {'OBJECTID': polys['properties']['OBJECTID'],
                                                         'Shape_Leng': boundary.length,
                                                         'Shape_Area': boundary.area,
                                                         'Max_Depth': 0}})

                elif polys['geometry']['type'] == 'Polygon':
                    # Identify the boundary of each Polygon
                    boundary = (shape(polys['geometry'])).boundary
                    if boundary.type== 'MultiLineString':
                        # Iterate over the LineStrings in each MultiLineString
                        for line in boundary:
                            # Save each LineString to the lines shapefile
                            output.write({'geometry': mapping(line),
                                          'type': line.geom_type,
                                          'properties': {'OBJECTID': polys['properties']['OBJECTID'],
                                                        'Shape_Leng': line.length,
                                                        'Shape_Area': line.area,
                                                        'Max_Depth': 0}})
                    elif boundary.type== 'LineString':
                        # Save each LineString to the lines shapefile
                        output.write({'geometry': mapping(boundary),
                                      'type': boundary.geom_type,
                                      'properties': {'OBJECTID': polys['properties']['OBJECTID'],
                                                    'Shape_Leng':boundary.length,
                                                    'Shape_Area': boundary.area,
                                                    'Max_Depth': 0}})


    """
    for elem in boundary:
        reconstruct = shape(elem['geometry'])
        print("elem")
        print(elem_bound['geometry']['type'])
        if elem['geometry']['type']== 'MultiLineString':
            print("Inner if statement)")
            for line in reconstruct:
                output.write({'geometry':mapping(line), 'properties':elem['properties']})
        elif elem['geometry']['type']=='LineString':
            output.write({'geometry':mapping(reconstruct), 'properties':elem['properties']})
            print("In elif")
    """

