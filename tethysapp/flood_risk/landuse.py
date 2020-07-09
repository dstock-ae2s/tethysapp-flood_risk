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


"""
Function which joins tax parcel values to building inundation shapefile
"""
def land_join(objectid_name, landid_name, land_val, f_path):
    # Set the working directory and find building inundation shapefile
    file_name = "Parcel_Inundation"
    SHP_DIR = "/home/dstock/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/"+file_name+'/'
    os.chdir(SHP_DIR)
    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(".shp"):
            shapefile = os.path.join(SHP_DIR, file)

    # Read in building inundation and land use shapefiles as GeoDataFrames
    join_file = gpd.GeoDataFrame.from_file(f_path)
    print("Join file")
    print(join_file.head())
    print(join_file.dtypes)
    target_file = gpd.GeoDataFrame.from_file(shapefile)
    print("Target file")
    print(target_file.head())
    print(target_file.dtypes)

    # Spatially join building inundation and land use parcels
    buildings_with_tax = sjoin(join_file, target_file, how='right', op='intersects')
    print("SJOIN")
    print(buildings_with_tax.head())
    print(buildings_with_tax.dtypes)

    # Dissolve joined file by land id
    buildings_with_tax=buildings_with_tax[[str(land_val), str(landid_name), 'geometry']]
    agg_bldgs_with_tax = buildings_with_tax.dissolve(by=str(landid_name), aggfunc='first')
    print("DISSOLVE")
    print(agg_bldgs_with_tax.head())
    print(agg_bldgs_with_tax.dtypes)

    # Spatially join building inundation and dissolved joined file
    bldgs_depth_tax = sjoin(agg_bldgs_with_tax, target_file, how='right', op='intersects')
    print("SJOIN2")
    print(bldgs_depth_tax.head())
    print(bldgs_depth_tax.dtypes)

    # Group by objectid to take the mode of the land use type in each objectid
    agg_bldgs_depth_tax = bldgs_depth_tax.groupby(str(objectid_name)).agg(
        USE1=(str(land_val), 'first'))
    print("DISSOLVE2")
    print(agg_bldgs_depth_tax.head())
    print(agg_bldgs_depth_tax.dtypes)

    # Merge file with total building value per objectid and mean depth per tax parcel with building inundation file
    target_file = target_file.merge(agg_bldgs_depth_tax, on=str(objectid_name))
    print("MERGE")
    print(target_file.head())
    print(target_file.dtypes)

    target_file = land_use(target_file, str(land_val))
    print("ADD COL")
    print(target_file.head())
    print(target_file.dtypes)

    # Check if the dataframe is empty and if not export to shapefile
    if target_file.empty:
        print("Dataframe is empty")
    else:
        file_name = "Landuse_Inundation"
        SHP_DIR = "/home/dstock/tethysapp-flood_risk/tethysapp/flood_risk/workspaces/user_workspaces/" + file_name + '/'
        try:
            os.mkdir(SHP_DIR)
        except OSError:
            print("Creation of the directory %s failed" % SHP_DIR)
        else:
            print("Successfully created the directory %s " % SHP_DIR)
        os.chdir(SHP_DIR)
        target_file.to_file("Landuse_Inundation.shp")

"""
Function which adds field to dataframe with a 1 indicating residential
"""
def land_use(target_file, land_val):
    target_file = target_file.rename(columns={land_val: 'Land_Use'})
    target_file.Land_Use.apply(str)

    old_land_val = land_val
    land_val = 'Land_Use'

    for idx, row in target_file.iterrows():
        if target_file.loc[idx, land_val]=='A' or target_file.loc[idx, land_val]=='G' or target_file.loc[idx, land_val]=='J':
            target_file.loc[idx, 'Residential'] = 1
        else:
            target_file.loc[idx, 'Residential'] = 0

    target_file = target_file.rename(columns={'Land_Use': old_land_val})
    return target_file
