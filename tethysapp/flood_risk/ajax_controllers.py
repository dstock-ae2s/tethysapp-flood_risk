from django.http import JsonResponse, HttpResponse, Http404
from tethys_sdk.gizmos import *
from .move_files import *
from .geoprocessing import *
from .max_depth import *
from .field_names import *
from .tax_parcel import *
from .landuse import *
from .streets import *
from .utilities import *
import geopandas as gpd
from geopandas.tools import sjoin

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
            is_buffer_empty = add_buffer(buffer_val, str(buildingid_field))

            if not is_buffer_empty:
                # Add max depth from raster to building boundary lines
                r_path = find_file("depth_file", ".tif")
                is_depth_empty = max_water_depth(r_path, buildingid_field, "depth_file")

                if not is_depth_empty:
                    # Add building value from tax parcels to building shapefile
                    f_path = find_file("tax_file", ".shp")
                    is_tax_empty = tax_join(buildingid_field, taxid_field, tax_field, f_path)

                    if not is_tax_empty:
                        # Add land use to building shapefile
                        f_path = find_file("landuse_file", ".shp")
                        land_join(buildingid_field, landuseid_field, landuse_field, f_path)
                        output_path = find_file("Landuse_Inundation", ".shp")
                        if not os.stat(output_path).st_size == 0:
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

        buffer_lines(streetid, buffer_val, output_file, output_file2)
        max_water_depth2(streetid, output_file, output_file2, output_file, 'Max_Depth')

        return JsonResponse(return_obj)


"""
Ajax controller which imports manhole shapefiles to the user workspace
"""


def manhole_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        manholeid = request.POST["manholeid_field"]

        buffer_val = 0.5

        simple_buffer(manholeid, buffer_val, "manhole_file", "Manhole_buffered", 'Polygon', 'Point')
        simple_max_water_depth(manholeid, "manhole_file", "Manhole_buffered", "Manhole_Inundation", 'Max_Depth', manholeid)

        buffer_val = request.POST["buffer"]
        if buffer_val == "":
            buffer_val = 20
        simple_buffer(manholeid, buffer_val, "manhole_file", "Manhole_radius", 'Polygon', 'Point')

        mh_inun = find_file("Manhole_Inundation", ".shp")
        mh_inun = gpd.GeoDataFrame.from_file(mh_inun)

        f_path = find_file("Streets_Inundation", ".shp")
        join_file = gpd.GeoDataFrame.from_file(f_path)
        join_file = join_file.rename(columns={'Max_Depth': 'Street_Depth'})
        if manholeid in join_file.columns:
            join_file = join_file.drop(columns=[manholeid])

        shapefile = find_file("Manhole_radius", ".shp")
        target_file = gpd.GeoDataFrame.from_file(shapefile)
        target_file = target_file.rename(columns={'Max_Depth': 'Blank_Field'})



        # Spatially join street inundation and tax parcels
        manholes_with_streets = sjoin(join_file, target_file, how='right', op='intersects')

        # Group by objectid to take the max street depth for each manhole objectid
        agg_manhole_street_depth = manholes_with_streets.groupby(str(manholeid)).agg(
            Blank_Field=('Blank_Field', 'mean'),
            Street_Depth=('Street_Depth', 'max'))

        # Merge file with manhole file per objectid
        mh_inun = mh_inun.merge(agg_manhole_street_depth, on=str(manholeid))
        mh_inun = mh_inun.rename(columns={'Max_Depth': 'MH_Depth'})

        for idx, row in target_file.iterrows():
            if mh_inun.loc[idx, 'MH_Depth'] < 0 and mh_inun.loc[idx, 'Street_Depth'] == 0:
                mh_inun.loc[idx, 'Blank_Field'] = "Not in ROW"
            elif mh_inun.loc[idx, 'MH_Depth'] > 0:
                mh_inun.loc[idx, 'Blank_Field'] = "Storm Sewer Controlled"
            elif mh_inun.loc[idx, 'MH_Depth'] <= 0 and mh_inun.loc[idx, 'Street_Depth'] < 0.5:
                mh_inun.loc[idx, 'Blank_Field'] = "OK"
            elif mh_inun.loc[idx, 'MH_Depth'] <= 0 and mh_inun.loc[idx, 'Street_Depth'] >= 0.5:
                mh_inun.loc[idx, 'Blank_Field'] = "Inlet Controlled"
            else:
                mh_inun.loc[idx, 'Blank_Field'] = "Not in ROW"

        if not mh_inun.empty:
            mk_change_directory("MH_Street_Inundation")
            mh_inun.to_file("MH_Street_Inundation.shp")

        output_path = find_file("MH_Street_Inundation", ".shp")
        if not os.stat(output_path).st_size == 0:
            move_geoserver("MH_Street_Inundation")


        return JsonResponse(return_obj)

