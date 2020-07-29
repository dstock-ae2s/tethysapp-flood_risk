from django.http import JsonResponse, HttpResponse, Http404
from tethys_sdk.gizmos import *
from .utilities import *
import geopandas as gpd
from geopandas.tools import sjoin
import math

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

                            #f_path = find_file("tax_file", ".shp")
                            #is_tax_empty = tax_join(buildingid_field, taxid_field, tax_field, f_path)

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
                    mk_change_directory("Streets_Inundation")
                    streets_with_depth.to_file(filename=("Streets_Inundation.shp"))

        return JsonResponse(return_obj)


"""
Ajax controller which determines if storm sewer or inlet controlled
"""


def manhole_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        manholeid = request.POST["manholeid_field"]
        buffer_val = 0.5

        add_buffer(manholeid, buffer_val, "manhole_file", "Manhole_buffered", 'Polygon', 'Point')
        max_int_results = max_intersect("Manhole_buffered", "depth_file")
        if not max_int_results['is_dataframe_empty']:
            raster_stats_dataframe = max_int_results['return_dataframe']
            print("RASTER STATS")
            print(raster_stats_dataframe.dtypes)
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
        #simple_max_water_depth(manholeid, "manhole_file", "Manhole_buffered", "Manhole_Inundation", 'Max_Depth', manholeid)

                if not os.stat(find_file("Manhole_Inundation", ".shp")).st_size == 0:
                    buffer_val = request.POST["buffer"]
                    if buffer_val == "":
                        buffer_val = 20
                    add_buffer(manholeid, buffer_val, "manhole_file", "Manhole_radius", 'Polygon', 'Point')

                    mh_inun = find_file("Manhole_Inundation", ".shp")
                    mh_inun = gpd.GeoDataFrame.from_file(mh_inun)

                    f_path = find_file("Streets_Inundation", ".shp")
                    join_file = gpd.GeoDataFrame.from_file(f_path)
                    join_file = join_file.rename(columns={'Max_Depth': 'Street_Depth'})
                    if manholeid in join_file.columns:
                        join_file = join_file.drop(columns=[manholeid, 'Shape_Leng', 'Shape_Area'])

                    shapefile = find_file("Manhole_radius", ".shp")
                    target_file = gpd.GeoDataFrame.from_file(shapefile)

                    # Spatially join street inundation and tax parcels
                    manholes_with_streets = sjoin(join_file, target_file, how='right', op='intersects')

                    # Group by objectid to take the max street depth for each manhole objectid
                    agg_manhole_street_depth = manholes_with_streets.groupby(str(manholeid)).agg(
                        Street_Depth=('Street_Depth', 'max'))

                    # Merge file with manhole file per objectid
                    mh_inun = mh_inun.merge(agg_manhole_street_depth, on=str(manholeid))
                    mh_inun = mh_inun.rename(columns={'Max_Depth': 'MH_Depth'})

                    for idx, row in mh_inun.iterrows():
                        if mh_inun.loc[idx, 'MH_Depth'] == 0 and mh_inun.loc[idx, 'Street_Depth'] == 0:
                            mh_inun.loc[idx, 'Control'] = "Not in ROW"
                        elif mh_inun.loc[idx, 'MH_Depth'] <= 0 and mh_inun.loc[idx, 'Street_Depth'] < 0.5:
                            mh_inun.loc[idx, 'Control'] = "OK"
                        elif mh_inun.loc[idx, 'MH_Depth'] <= 0 and mh_inun.loc[idx, 'Street_Depth'] >= 0.5:
                            mh_inun.loc[idx, 'Control'] = "Inlet Controlled"
                        elif mh_inun.loc[idx, 'MH_Depth'] > 0:
                            mh_inun.loc[idx, 'Control'] = "Storm Sewer Controlled"
                        else:
                            mh_inun.loc[idx, 'Control'] = "Not in ROW"

                    if not mh_inun.empty:
                        mk_change_directory("MH_Street_Inundation")
                        mh_inun.to_file("MH_Street_Inundation.shp")

                    output_path = find_file("MH_Street_Inundation", ".shp")
                    if not os.stat(output_path).st_size == 0:
                        move_geoserver("MH_Street_Inundation")

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
        street_flow = request.POST["street_flow"]
        buffer = float(request.POST["buffer"])
        distance = float(request.POST["distance"])
        mannings_n = float(request.POST["mannings_n"])

        street_file = "street2_file"
        split_street_file = "Streets2_divided"
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

            add_buffer(pipeid, buffer, pipe_file, pipe_buffered_file, 'Polygon', 'LineString')

            # Spatially join buffered street flow and pipe flow
            f_path = find_file(street_file, ".shp")
            left_file = gpd.GeoDataFrame.from_file(f_path)
            left_file = left_file.rename(columns={streetid: 'STREETID'})

            f_path = find_file(pipe_buffered_file, ".shp")
            buffer_file = gpd.GeoDataFrame.from_file(f_path)

            # Edit file to include all fields
            this_input = gpd.read_file(find_file(pipe_file, ".shp"))
            this_input = this_input.drop(columns=['geometry'])
            this_input.fillna(0, inplace=True)

            right_file = buffer_file.merge(this_input, on=pipeid)
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

            agg_streets_and_pipes['Q_req'] = (agg_streets_and_pipes[flow] + agg_streets_and_pipes[street_flow]) - agg_streets_and_pipes['Design_Q']

            for i, j in agg_streets_and_pipes.iterrows():
                if agg_streets_and_pipes.loc[i, 'Q_req'] < 0:
                    agg_streets_and_pipes.loc[i, 'New_Dia'] = ''
                else:
                    this_slope = agg_streets_and_pipes.loc[i, slope]
                    q_req = agg_streets_and_pipes.loc[i, 'Q_req'] + agg_streets_and_pipes.loc[i, 'Design_Q']
                    agg_streets_and_pipes.loc[i, 'New_Dia'] = (math.pow(
                        q_req * (mannings_n / 1.486) * (math.pow(4, 5 / 3) / math.pi) * (
                                    1 / math.pow(this_slope, 1 / 2)), 3 / 8))

            # Check if the dataframe is empty and if not export to shapefile
            if not agg_streets_and_pipes.empty:
                mk_change_directory("Pipe_Inundation")
                agg_streets_and_pipes.to_file(filename=("Pipe_Inundation.shp"), overwrite=True)

        return JsonResponse(return_obj)
