from django.http import JsonResponse, HttpResponse, Http404
from tethys_sdk.gizmos import *
from .utilities import *
import geopandas as gpd
from geopandas.tools import sjoin
import math
from pyproj import Proj, transform
from django.shortcuts import render, reverse
import geojson
import fiona

def file_upload(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        filetype = request.POST["filetype"]
        file_name = request.POST["file_name"]
        shapefiles = request.FILES.getlist('shapefile')

        field_names = move_files_get_fields(shapefiles, file_name, filetype)
        field_names = json.loads(field_names)
        return_obj["field_names"] = field_names["field_names"]

        return JsonResponse(return_obj)

def file_upload_move_files(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        file_name = request.POST["file_name"]
        shapefiles = request.FILES.getlist('shapefile')

        move_files(shapefiles, file_name)

        return_obj['success'] = "success"

        return JsonResponse(return_obj)


"""
Ajax controller which imports building shapefiles to the user workspace
"""
def building_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        # Import text entries and field names
        buffer_val = request.POST["buffer"]
        if buffer_val=="":
            buffer_val = 1
        buildingid_field = request.POST["buildingid_field"]
        taxid_field = request.POST["taxid_field"]
        tax_field = request.POST["tax_field"]
        landuseid_field = request.POST["landuseid_field"]
        landuse_field = request.POST["landuse_field"]


        # Output building boundaries from building polygons shapefile
        f_path = find_file("bldg_file", ".shp")
        is_line_empty = polygon_to_line(f_path, "bldg_file", str(buildingid_field))
        if not is_line_empty:
            # Buffer lines shapefile to create polygons
            is_buffer_empty = add_buffer(str(buildingid_field), float(buffer_val), 'Building_Outlines', 'Bldg_Outline_Polygons', 'Polygon', 'LineString')

            if not is_buffer_empty:
                # Add max depth from raster to building boundary lines

                max_int_results = max_intersect("Bldg_Outline_Polygons", "depth_file")
                if not max_int_results['is_dataframe_empty']:
                    raster_stats_dataframe = max_int_results['return_dataframe']
                    raster_stats_dataframe['Max_Depth'] = raster_stats_dataframe['max']
                    raster_stats_dataframe = raster_stats_dataframe[[buildingid_field, 'Max_Depth']]
                    raster_stats_dataframe.fillna(0, inplace=True)
                    raster_stats_table = raster_stats_dataframe.groupby(str(buildingid_field)).agg(
                        Max_Depth=('Max_Depth', 'max'))

                    # Read in building shapefile and fill null values with 0
                    building_file = gpd.read_file(f_path)
                    building_file.fillna(0, inplace=True)

                    # Merge original buildings dataframe with depth table, then export as shapefile
                    buildings_with_depth = building_file.merge(raster_stats_table, on=str(buildingid_field))
                    if not buildings_with_depth.empty:
                        mk_change_directory("Buildings_Inundation")
                        buildings_with_depth.to_file(filename="Building_Inundation.shp")
                        if not os.stat(find_file("Buildings_Inundation", ".shp")).st_size == 0:
                            is_depth_empty = False

                        if not is_depth_empty:
                            # Add building value from tax parcels to building shapefile
                            is_tax_empty = True
                            join_file = gpd.GeoDataFrame.from_file(find_file("tax_file", ".shp"))
                            target_file = gpd.GeoDataFrame.from_file(find_file("Buildings_Inundation", ".shp"))
                            buildings_with_tax = sjoin(join_file, target_file, how='right', op='intersects')
                            buildings_with_tax = buildings_with_tax[['Max_Depth', str(tax_field), str(taxid_field), 'geometry']]
                            agg_bldgs_with_tax = buildings_with_tax.dissolve(by=str(taxid_field), aggfunc='mean')
                            agg_bldgs_with_tax=agg_bldgs_with_tax.rename(columns={'Max_Depth': 'Mean_Depth'})
                            bldgs_depth_tax = sjoin(agg_bldgs_with_tax, target_file, how='right', op='intersects')
                            agg_bldgs_depth_tax = bldgs_depth_tax.groupby(str(buildingid_field)).agg(
                                Mean_Depth = ('Mean_Depth','mean'),
                                BLDGVAL = (str(tax_field), 'sum'))
                            target_file = target_file.merge(agg_bldgs_depth_tax, on=str(buildingid_field))
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
                            if not target_file.empty:
                                mk_change_directory("Parcel_Inundation")
                                target_file.to_file("Parcel_Inundation.shp")
                                if not os.stat(find_file("Parcel_Inundation", ".shp")).st_size == 0:
                                    is_tax_empty = False

                            if not is_tax_empty:
                                # Add land use to building shapefile
                                join_file = gpd.GeoDataFrame.from_file(find_file("landuse_file", ".shp"))
                                target_file = gpd.GeoDataFrame.from_file(find_file("Parcel_Inundation", ".shp"))
                                buildings_with_tax = sjoin(join_file, target_file, how='right', op='intersects')
                                buildings_with_tax = buildings_with_tax[[str(landuse_field), str(landuseid_field), 'geometry']]
                                agg_bldgs_with_tax= buildings_with_tax.dissolve(by=str(landuseid_field), aggfunc='first')
                                bldgs_depth_tax = sjoin(agg_bldgs_with_tax, target_file, how='right', op='intersects')
                                agg_bldgs_depth_tax=bldgs_depth_tax.groupby(str(buildingid_field)).agg(
                                    USE1=(str(landuse_field), 'first'))
                                target_file = target_file.merge(agg_bldgs_depth_tax, on=str(buildingid_field))
                                target_file = target_file.rename(columns={landuse_field:'Land_Use'})
                                target_file.Land_Use.apply(str)
                                for idx, row in target_file.iterrows():
                                    if target_file.loc[idx, 'Land_Use'] == 'A' or target_file.loc[idx, 'Land_Use'] == 'G' or target_file.loc[idx, 'Land_Use'] == 'J':
                                        target_file.loc[idx, 'Residential'] = 1
                                    else:
                                        target_file.loc[idx, 'Residential'] = 0
                                target_file=target_file.rename(columns={'Land_Use':landuse_field})
                                return_obj["bounds"] = target_file.total_bounds
                                if not target_file.empty:
                                    mk_change_directory("Landuse_Inundation")
                                    target_file.to_file("Landuse_Inundation.shp")

                                    if not os.stat(find_file("Landuse_Inundation", ".shp")).st_size == 0:
                                        move_geoserver("Landuse_Inundation")

        return JsonResponse(return_obj)



"""
Ajax controller which imports streets shapefiles to the user workspace
"""


def streets_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':
        streetid = request.POST["streetid_field"]

        buffer_val = request.POST["buffer"]
        if buffer_val == "":
            buffer_val = 20
        distance_val = request.POST["distance"]

        file_name = "street_file"
        output_file = "Streets_divided"
        output_file2 = "Streets_buffered"

        # Split streets at set distance interval
        divide_lines(str(streetid), float(distance_val), file_name, output_file)

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

            add_buffer(streetid, buffer_val, output_file, output_file2, 'Polygon', 'LineString')
            max_int_results = max_intersect(output_file2, "depth_file")
            if not max_int_results['is_dataframe_empty']:
                raster_stats_dataframe = max_int_results['return_dataframe']
                raster_stats_dataframe['Max_Depth'] = raster_stats_dataframe['max']
                raster_stats_dataframe.fillna(0, inplace=True)
                raster_stats_dataframe = raster_stats_dataframe[['Index', 'Max_Depth']]
                streets_divided = gpd.read_file(find_file("Streets_divided", ".shp"))
                streets_divided.fillna(0, inplace=True)
                streets_with_depth = streets_divided.merge(raster_stats_dataframe, on='Index')

                if not streets_with_depth.empty:
                    inProj = Proj(init=streets_with_depth.crs)
                    outProj = Proj(init='epsg:4326')
                    this_extent = (streets_with_depth.total_bounds).tolist()
                    x1, y1 = this_extent[0], this_extent[1]
                    x1, y1 = transform(inProj, outProj, x1, y1)
                    x2, y2 = this_extent[2], this_extent[3]
                    x2, y2 = transform(inProj, outProj, x2, y2)
                    this_extent = [x1, y1, x2, y2]

                    this_centroid = centroid(this_extent)

                    return_obj["centroid"] = this_centroid
                    return_obj["extent"] = this_extent
                    return_obj["layer"] = 'flood-risk:Streets_Inundation'

                    mk_change_directory("Streets_Inundation")
                    streets_with_depth.to_file(filename=("Streets_Inundation.shp"))

                    # Convert all coordinates to EPSG:4326
                    print(streets_with_depth['geometry'].head())
                    streets_with_depth = streets_with_depth.to_crs("EPSG:3857")
                    print("TRANSFORM")
                    print(streets_with_depth['geometry'].head())
                    streets_with_depth.to_file(filename=("Streets_Inundation.geojson"), driver='GeoJSON')
                    mk_change_directory("Streets_Inundation")
                    streets_features = []
                    if not os.stat(find_file("Streets_Inundation", ".geojson")).st_size == 0:
                        print("In the if statement")
                        with fiona.open("Streets_Inundation.geojson") as data_file:
                            for data in data_file:
                                streets_features.append(data)
                            return_obj["streets_features"] = streets_features
                    # streets_features = []
                    # mk_change_directory("Streets_Inundation")
                    # if not os.stat(find_file("Streets_Inundation", ".geojson")).st_size == 0:
                    #     print("In the if statement")
                    #     with fiona.open("Streets_Inundation.geojson") as data_file:
                    #         layer_crs = (str(data_file.crs['init'])).upper()
                    #         print(layer_crs)
                    #
                    #         for data in data_file:
                    #             streets_features.append(data)
                    #
                    #         style = {'ol.style.Style': {
                    #             'stroke': {'ol.style.Stroke': {
                    #                 'color': 'red',
                    #                 'width': 20
                    #             }},
                    #             'fill': {'ol.style.Fill': {
                    #                 'color': 'green'
                    #             }},
                    #             'image': {'ol.style.Circle': {
                    #                 'radius': 10,
                    #                 'fill': None,
                    #                 'stroke': {'ol.style.Stroke': {
                    #                     'color': 'red',
                    #                     'width': 2
                    #                 }}
                    #             }}
                    #         }}
                    #
                    #         geojson_object = {
                    #             'type': 'FeatureCollection',
                    #             'crs': {
                    #                 'type': 'name',
                    #                 'properties': {
                    #                     'name': layer_crs
                    #                 }
                    #             },
                    #             'features': streets_features
                    #         }
                    #
                    #         geojson_layer = MVLayer(
                    #             source='GeoJSON',
                    #             options=geojson_object,
                    #             layer_options={'style': style},
                    #             legend_title='Test GeoJSON',
                    #             legend_extent=[-46.7, -48.5, 74, 59],
                    #             legend_classes=[
                    #                 MVLegendClass('line', 'Lines', stroke='red')
                    #             ],
                    #         )
                    #         return_obj['streets_layer'] = geojson_layer

                    # if not os.stat(find_file("Streets_Inundation", ".shp")).st_size == 0:
                    #     move_geoserver("Streets_Inundation")


        return JsonResponse(return_obj)


"""
Ajax controller which determines if storm sewer or inlet controlled
"""


def manhole_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        street_depth = request.POST["street_depth"]
        f_path = find_file("mhstreet_file", ".shp")
        join_file = gpd.GeoDataFrame.from_file(f_path)
        print("At the Beginning")
        print(join_file.columns)

        manholeid = request.POST["manholeid_field"]
        buffer_val = 0.5

        add_buffer(manholeid, buffer_val, "manhole_file", "Manhole_buffered", 'Polygon', 'Point')
        max_int_results = max_intersect("Manhole_buffered", "depth_file")
        if not max_int_results['is_dataframe_empty']:
            raster_stats_dataframe = max_int_results['return_dataframe']
            raster_stats_dataframe['Max_Depth']=raster_stats_dataframe['max']
            raster_stats_dataframe = raster_stats_dataframe.drop(columns=['max', 'geometry'])
            target_file = gpd.read_file(find_file("manhole_file", ".shp"))
            target_file.fillna(0, inplace=True)
            if 'Max_Depth' in target_file.columns:
                target_file=target_file.drop(columns=['Max_Depth'])

            manholes_with_depth = target_file.merge(raster_stats_dataframe, on=manholeid)
            if not manholes_with_depth.empty:
                mk_change_directory("Manhole_Inundation")
                manholes_with_depth.to_file(filename="Manhole_Inundation.shp")

                if not os.stat(find_file("Manhole_Inundation", ".shp")).st_size == 0:
                    buffer_val = request.POST["buffer"]
                    if buffer_val == "":
                        buffer_val = 20
                    add_buffer(manholeid, buffer_val, "manhole_file", "Manhole_radius", 'Polygon', 'Point')

                    mh_inun = find_file("Manhole_Inundation", ".shp")
                    mh_inun = gpd.GeoDataFrame.from_file(mh_inun)

                    street_depth = request.POST["street_depth"]
                    f_path = find_file("mhstreet_file", ".shp")
                    join_file = gpd.GeoDataFrame.from_file(f_path)
                    print("Before Rename")
                    print(join_file.columns)
                    print(str(street_depth))
                    join_file = join_file.rename(columns={str(street_depth): 'St_Depth'})
                    print(join_file.columns)
                    if manholeid in join_file.columns:
                        join_file = join_file.drop(columns=[manholeid, 'Shape_Leng', 'Shape_Area'])

                    shapefile = find_file("Manhole_radius", ".shp")
                    target_file = gpd.GeoDataFrame.from_file(shapefile)

                    # Spatially join street inundation and tax parcels
                    manholes_with_streets = sjoin(join_file, target_file, how='right', op='intersects')

                    # Group by objectid to take the max street depth for each manhole objectid
                    agg_manhole_street_depth = manholes_with_streets.groupby(str(manholeid)).agg(
                        St_Depth=('St_Depth', 'max'))

                    # Merge file with manhole file per objectid
                    mh_inun = mh_inun.merge(agg_manhole_street_depth, on=str(manholeid))
                    mh_inun = mh_inun.rename(columns={'Max_Depth': 'MH_Depth'})

                    for idx, row in mh_inun.iterrows():
                        if mh_inun.loc[idx, 'MH_Depth'] == 0 and mh_inun.loc[idx, 'St_Depth'] == 0:
                            mh_inun.loc[idx, 'Control'] = "Not in ROW"
                        elif mh_inun.loc[idx, 'MH_Depth'] <= 0 and mh_inun.loc[idx, 'St_Depth'] < 0.5:
                            mh_inun.loc[idx, 'Control'] = "OK"
                        elif mh_inun.loc[idx, 'MH_Depth'] <= 0 and mh_inun.loc[idx, 'St_Depth'] >= 0.5:
                            mh_inun.loc[idx, 'Control'] = "Inlet Controlled"
                        elif mh_inun.loc[idx, 'MH_Depth'] > 0:
                            mh_inun.loc[idx, 'Control'] = "Storm Sewer Controlled"
                        else:
                            mh_inun.loc[idx, 'Control'] = "Not in ROW"

                    if not mh_inun.empty:
                        inProj = Proj(init=mh_inun.crs)
                        outProj = Proj(init='epsg:4326')
                        this_extent = (mh_inun.total_bounds).tolist()
                        x1, y1 = this_extent[0], this_extent[1]
                        x1, y1 = transform(inProj, outProj, x1, y1)
                        x2, y2 = this_extent[2], this_extent[3]
                        x2, y2 = transform(inProj, outProj, x2, y2)
                        this_extent = [x1, y1, x2, y2]

                        this_centroid = centroid(this_extent)

                        return_obj["centroid"] = this_centroid
                        return_obj["extent"] = this_extent
                        mk_change_directory("MH_Street_Inundation")
                        mh_inun.to_file("MH_Street_Inundation.shp")

                    if not os.stat(find_file("MH_Street_Inundation", ".shp")).st_size == 0:
                        move_geoserver("MH_Street_Inundation")
                        return_obj["geoserver_layer"] = False

                        geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)
                        response = geoserver_engine.list_layers(with_properties=False)
                        if response['success']:
                            for layer in response['result']:
                                if layer == 'flood-risk:MH_Street_Inundation':
                                    geoserver_layer=[]
                                    """geoserver_layer = MVLayer(
                                        source='ImageWMS',
                                        options={
                                            'url': 'http://localhost:8080/geoserver/wms',
                                            'params': {'LAYERS': 'flood-risk:MH_Street_Inundation'},
                                            'serverType': 'geoserver'
                                        },
                                        legend_title=""
                                    )"""
                                    return_obj["geoserver_layer"] = True

        return JsonResponse(return_obj)


"""
Ajax controller which determines if pipes are undersized
"""


def pipe_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        pipeid = request.POST["pipeid_field"]
        flow = request.POST["flow"]
        diameter = request.POST["diameter"]
        slope = request.POST["slope"]
        streetid = request.POST["streetid_field"]
        buffer = float(request.POST["pipe_buffer"])
        distance = float(request.POST["distance"])
        mannings_n = float(request.POST["mannings_n"])
        pipe_rad = request.POST["pipe_rad"]

        street_file = "street2_file"
        split_street_file = "Streets2_divided"
        street_buffered_file = "Streets2_buffered"
        pipe_file = "pipe_file"
        pipe_buffered_file = "Pipes_buffered"

        # Split streets at set distance interval
        divide_lines(str(streetid), float(distance), street_file, split_street_file)

        # Edit file to include all fields
        this_output = gpd.read_file(find_file(split_street_file, ".shp"))
        this_output.fillna(0, inplace=True)

        this_input = gpd.read_file(find_file(street_file, ".shp"))
        this_input = this_input.drop(columns=['geometry'])
        this_input.fillna(0, inplace=True)

        streets_with_info = this_output.merge(this_input, on=streetid)

        # Check if the dataframe is empty and if not export to shapefile
        if not streets_with_info.empty:
            mk_change_directory(split_street_file)
            streets_with_info.to_file(filename=(split_street_file + ".shp"), overwrite=True)
            street_rad = request.POST["street_rad"]

            if street_rad == "no":
                street_flow = request.POST["street_flow"]
            else:
                street_flow = 's_flow'
                street_buffer = request.POST["street_buffer"]
                add_buffer(streetid, street_buffer, split_street_file, street_buffered_file, 'Polygon', 'LineString')
                output_intersect = max_intersect(street_buffered_file, "depth2_file")
                if not output_intersect["is_dataframe_empty"]:
                    raster_stats_dataframe = output_intersect["return_dataframe"]
                    raster_stats_dataframe[street_flow] = raster_stats_dataframe['max']
                    raster_stats_dataframe = raster_stats_dataframe.drop(columns=['max', 'geometry', 'Shape_Leng', 'Shape_Area'])
                    target_file = gpd.read_file(find_file(split_street_file, ".shp"))
                    target_file.fillna(0, inplace=True)
                    if street_flow in target_file.columns:
                        target_file = target_file.drop(columns=[street_flow, 'Shape_Leng', 'Shape_Area'])

                    street_with_flow = target_file.merge(raster_stats_dataframe, on=streetid)
                    split_street_file = "Street_Flow"
                    if not street_with_flow.empty:
                        mk_change_directory(split_street_file)
                        street_with_flow.to_file(filename=split_street_file+".shp")

            if not os.stat(find_file(split_street_file, ".shp")).st_size == 0:
                add_buffer(pipeid, buffer, pipe_file, pipe_buffered_file, 'Polygon', 'LineString')

                # Spatially join street flow and buffered pipe flow
                f_path = find_file(split_street_file, ".shp")
                left_file = gpd.GeoDataFrame.from_file(f_path)
                left_file = left_file.rename(columns={streetid: 'STREETID'})

                f_path = find_file(pipe_buffered_file, ".shp")
                buffer_file = gpd.GeoDataFrame.from_file(f_path)
                buffer_file = buffer_file.drop(columns=['geometry'])

                # Edit file to include all fields
                this_input = gpd.read_file(find_file(pipe_file, ".shp"))
                this_input.fillna(0, inplace=True)

                right_file = this_input.merge(buffer_file, on=pipeid)
                right_file = right_file.rename(columns={pipeid: 'PIPEID'})

                streets_and_pipes = sjoin(left_file, right_file, how='right', op='intersects')
                streets_and_pipes.fillna(0, inplace=True)
                streets_and_pipes = streets_and_pipes.drop(columns=['index_left'])

                agg_streets_and_pipes = streets_and_pipes.dissolve(by='PIPEID', aggfunc='max')

                for i, j in agg_streets_and_pipes.iterrows():
                    this_diameter = float(agg_streets_and_pipes.loc[i, diameter])
                    this_slope = float(agg_streets_and_pipes.loc[i, slope])
                    agg_streets_and_pipes.loc[i, 'Design_Q'] = (1.486 / mannings_n) * math.pi * math.pow(this_diameter, 2) * 0.25 * math.pow(
                        this_diameter * 0.25, 2 / 3) * math.pow(this_slope, 0.5)

                if street_flow in agg_streets_and_pipes.columns:
                    if pipe_rad == "yes":
                        agg_streets_and_pipes['Q_req'] = (agg_streets_and_pipes[flow] + agg_streets_and_pipes[street_flow]) - agg_streets_and_pipes['Design_Q']
                    else:
                        agg_streets_and_pipes['Q_req'] = (agg_streets_and_pipes[street_flow]) - agg_streets_and_pipes['Design_Q']

                    diameter_options = [0.010417, 0.020833, 0.03125, 0.041667, 0.0625, 0.083333, 0.104167, 0.125,
                                        0.166667, 0.208333, 0.25, 0.291667, 0.333333, 0.375, 0.416667, 0.5, 0.583333,
                                        0.666667, 0.75, 0.833333, 0.916667, 1, 1.166667, 1.333333, 1.5, 1.66667,
                                        1.833333, 2, 2.166667, 2.333333, 2.5, 2.666667, 2.833333, 3, 3.166667, 3.333333,
                                        3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 10, 12]

                    for i, j in agg_streets_and_pipes.iterrows():
                        if agg_streets_and_pipes.loc[i, 'Q_req'] < 0:
                            agg_streets_and_pipes.loc[i, 'Dia_req'] = ''
                            agg_streets_and_pipes.loc[i, 'Dia_sugg'] = agg_streets_and_pipes.loc[i, diameter]
                        else:
                            this_slope = agg_streets_and_pipes.loc[i, slope]
                            q_req = agg_streets_and_pipes.loc[i, 'Q_req'] + agg_streets_and_pipes.loc[i, 'Design_Q']
                            agg_streets_and_pipes.loc[i, 'Dia_req'] = (math.pow(
                                q_req * (mannings_n / 1.486) * (math.pow(4, 5 / 3) / math.pi) * (
                                            1 / math.pow(this_slope, 1 / 2)), 3 / 8))
                            if agg_streets_and_pipes.loc[i, 'Dia_req'] > 12:
                                new_diameter = agg_streets_and_pipes.loc[i, 'Dia_req']
                            else:
                                absolute_difference_function = lambda list_value: abs(list_value-agg_streets_and_pipes.loc[i, 'Dia_req'])
                                new_diameter = min(diameter_options, key=absolute_difference_function)
                                if new_diameter < agg_streets_and_pipes.loc[i, 'Dia_req']:
                                    new_diameter = diameter_options[(diameter_options.index(new_diameter)+1)]
                            agg_streets_and_pipes.loc[i, 'Dia_sugg'] = new_diameter
    
                    # Check if the dataframe is empty and if not export to shapefile
                    if not agg_streets_and_pipes.empty:
                        mk_change_directory("Pipe_Inundation")
                        agg_streets_and_pipes.to_file(filename=("Pipe_Inundation.shp"), overwrite=True)
                        if not os.stat(find_file("Pipe_Inundation", ".shp")).st_size == 0:
                            move_geoserver("Pipe_Inundation")

        return JsonResponse(return_obj)
