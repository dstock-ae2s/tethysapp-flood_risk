from shapely.geometry import mapping, shape
import fiona
import os
from collections import OrderedDict
from shapely.geometry import MultiPolygon, Point, shape, mapping, LineString, Polygon
from shapely import wkt
import rasterio
from rasterio.features import shapes
import rasterstats as rs
import numpy as np
from osgeo import gdal
import geopandas as gpd
from geopandas.tools import sjoin
from .utilities import *


"""
Function which joins tax parcel values to building inundation shapefile
"""
def tax_join(objectid_name, taxid_name, tax_val, f_path):
    not_empty_file = True

    # Set the working directory and find building inundation shapefile
    file_name = "Buildings_Inundation"
    SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/"+file_name+'/'
    os.chdir(SHP_DIR)
    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(".shp"):
            shapefile = os.path.join(SHP_DIR, file)

    # Read in building inundation and tax parcel shapefiles as GeoDataFrames
    join_file = gpd.GeoDataFrame.from_file(f_path)
    target_file = gpd.GeoDataFrame.from_file(shapefile)

    # Spatially join building inundation and tax parcels
    buildings_with_tax = sjoin(join_file, target_file, how='right', op='intersects')

    # Dissolve joined file by tax id and take the mean depth in the tax parcel
    buildings_with_tax=buildings_with_tax[['Max_Depth', str(tax_val), str(taxid_name), 'geometry']]
    agg_bldgs_with_tax = buildings_with_tax.dissolve(by=str(taxid_name), aggfunc='mean')
    agg_bldgs_with_tax = agg_bldgs_with_tax.rename(columns={'Max_Depth': 'Mean_Depth'})

    # Spatially join building inundation and dissolved joined file
    bldgs_depth_tax = sjoin(agg_bldgs_with_tax, target_file, how='right', op='intersects')

    # Group by objectid to take the sum of the building values in each objectid
    agg_bldgs_depth_tax = bldgs_depth_tax.groupby(str(objectid_name)).agg(
        Mean_Depth=('Mean_Depth', 'mean'),
        BLDGVAL=(str(tax_val), 'sum'))

    # Merge file with total building value per objectid and mean depth per tax parcel with building inundation file
    target_file = target_file.merge(agg_bldgs_depth_tax, on=str(objectid_name))

    target_file = value_lost(target_file)

    # Check if the dataframe is empty and if not export to shapefile
    if not target_file.empty:
        file_name = "Parcel_Inundation"
        SHP_DIR = "/home/dstock/tethysdev/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        try:
            os.mkdir(SHP_DIR)
        except OSError:
            print("Creation of the directory %s failed" % SHP_DIR)
        else:
            print("Successfully created the directory %s " % SHP_DIR)
        os.chdir(SHP_DIR)
        target_file.to_file("Parcel_Inundation.shp")


        output_path = find_file("Parcel_Inundation", ".shp")
        if not os.stat(output_path).st_size == 0:
            not_empty_file = False

    return not_empty_file

"""
Function which adds field to dataframe calculating building value lost due to flood depth
"""
def value_lost(target_file):
    target_file = target_file.rename(columns={'Max_Depth': 'Lost_Value'})
    for idx, row in target_file.iterrows():
        if 0 < target_file.loc[idx, 'Mean_Depth'] < 0.5:
            target_file.loc[idx, 'Lost_Value'] = 0.25 * target_file.loc[idx, 'BLDGVAL']
        elif 0.5 < target_file.loc[idx, 'Mean_Depth'] < 1:
            target_file.loc[idx, 'Lost_Value'] = 0.5 * target_file.loc[idx, 'BLDGVAL']
        elif target_file.loc[idx, 'Mean_Depth'] > 1:
            target_file.loc[idx, 'Lost_Value'] = 0.75 * target_file.loc[idx, 'BLDGVAL']
        else:
            target_file.loc[idx, 'Lost_Value'] = 0
    return target_file
