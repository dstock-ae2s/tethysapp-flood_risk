/*
Declaring global variables
*/
var buffer; //Buffer around manholes to pull max depth from
var distance; //Road segment length
var manholeid_field; //ID of manhole from input shapefile
var previous_size; //Size of map contained within map div

/*
Function to upload input files without fields to the user workspace
*/
function uploadFileNoFields(file_upload_id, file_name){
    var shapefiles = $(file_upload_id)[0].files;

    //Preparing data to be submitted via AJAX POST request
    var data = new FormData();
    data.append("file_name", file_name);
    for (var i=0; i< shapefiles.length; i++){
        data.append("shapefile", shapefiles[i])
    }

    file_upload_process_no_fields(file_upload_id, data);
};

/*
Helper function
Passes files without fields to the ajax to be uploaded to the user workspace
*/
function file_upload_process_no_fields(file_upload_id, data){
    var file_upload = ajax_update_database_with_file("file-upload-move-files", data); //Submitting the data through the ajax function, see main.js for the helper function.
    file_upload.done(function(return_data){
        if("success" in return_data){
            var file_upload_button = $(file_upload_id);
            var file_upload_button_html = file_upload_button.html();
            file_upload_button.text('File Uploaded');
        };
    });
};

/*
Function to upload input files with fields to the user workspace
*/
function uploadFile(file_upload_id, file_name, filetype, number_fields){

    var shapefiles = $(file_upload_id)[0].files;

    //Preparing data to be submitted via AJAX POST request
    var data = new FormData();
    data.append("file_name", file_name);
    data.append("filetype", filetype);
    for (var i=0; i< shapefiles.length; i++){
        data.append("shapefile", shapefiles[i])
    }
    var field_list=[]
    for (var j=0; j<number_fields; j++){
        var n = file_name.slice(0,(file_name.search("_")));
        field_list[j] = n+'-field-select-'+(j);
    }
    console.log(field_list);

    file_upload_process(data, field_list);
};

/*
Helper function
Passes files with fields to the ajax to be uploaded to the user workspace
*/
function file_upload_process(data, field_list){
    var file_upload = ajax_update_database_with_file("file-upload", data); //Submitting the data through the ajax function, see main.js for the helper function.
    file_upload.done(function(return_data){ //Reset the form once the data is added succesfully
        if("field_names" in return_data){
            var options = return_data.field_names;
            console.log(options);
            console.log(field_list);
            for(var j=0; j < field_list.length; j++){
                console.log(field_list.length);
                var select = document.getElementById(field_list[j]);

                // Clear all existing options first:
                select.innerHTML = "<option value=\"" + "Select Field" + "\">" + "Select Field" + "</option>";

                // Populate list with options:
                for(var i = 0; i < options.length; i++){
                    var opt = options[i];
                    select.innerHTML += "<option value=\"" + opt + "\">" + opt + "</option>";
                }
            };
        };
    });
};

/*
Function which extracts flood depths over manholes from raster
and compares this with street flood depth to determine if manholes
are inlet or storm sewer controlled
*/
process_manhole = function(data) {

    var data = new FormData();

    // Read in input values
    manholeid_field = document.getElementById("manhole-field-select-0").value;
    data.append("manholeid_field", manholeid_field)

    street_depth = document.getElementById("mhstreet-field-select-0").value;
    data.append("street_depth", street_depth)

    buffer = document.getElementById("manhole-buffer").value;
    data.append("buffer", buffer);

    // Check for errors in input values
    sum_check = (check(buffer, "manhole-buffer-error")
                +check(manholeid_field, "manhole-field-select-0-error")
                +check(street_depth, "mhstreet-field-select-0-error"))


    if(sum_check == 0){
        var manhole_risk = ajax_update_database_with_file("manhole-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
            manhole_risk.done(function(return_data){
                ol_map = TETHYS_MAP_VIEW.getMap();
                document.getElementById("manhole_map").classList.remove("hideDiv"); // Show the map
                ol_map.setSize(previous_size); // Resize the map to fit the div
                ol_map.renderSync(); // Update the map
                (document.getElementsByClassName("collapsible"))[0].click(); // Collapse input menu div

                // Style manhole layer
                var styles = [
                    new ol.style.Style({
                        image: new ol.style.Circle({
                            radius: 5,
                            fill: new ol.style.Fill({
                                color: 'red',
                            }),
                        }),
                    })
                ];

                // Create a geojson object holding manhole features
                var geojson_object = {
                    'type': 'FeatureCollection',
                    'crs': {
                        'type': 'name',
                        'properties': {
                            'name': 'EPSG:3857'
                        }
                    },
                    'features': return_data.mh_features
                };

                // Convert from geojson to openlayers collection
                var these_features = new ol.format.GeoJSON().readFeatures(geojson_object);

                // Create a new ol source and assign manhole features
                var vectorSource = new ol.source.Vector({
                    features: these_features
                });

                // Create a new modifiable layer and assign source and style
                var manholeLayer = new ol.layer.Vector({
                    name: 'Manholes',
                    source: vectorSource,
                    style: styles,
                });

                // Add manholes layer to map
                ol_map = TETHYS_MAP_VIEW.getMap();
                ol_map.addLayer(manholeLayer);
                ol_map = TETHYS_MAP_VIEW.getMap();

                // Define a new legend
                var legend = new ol.control.Legend({
                    title: 'Legend',
                    margin: 5,
                    collapsed: false
                });
                ol_map.addControl(legend);
                legend.addRow({
                    title: 'Manholes',
                    typeGeom:'Point',
                    style: new ol.style.Style({
                        image: new ol.style.Circle({
                            radius: 5,
                            fill: new ol.style.Fill({
                                color: 'red',
                            }),
                        })
                    })
                });
                TETHYS_MAP_VIEW.zoomToExtent(return_data.extent) // Zoom to layer
            });
    }
}

/*
Function to check input fields for errors and return 1 if errors are found
*/
function check(value, error_id){
    if(value.trim()==""){
        document.getElementById(error_id).innerHTML = "Field is not defined"
        return 1;
    }
    else if(value.trim() =="Select Field"){
        document.getElementById(error_id).innerHTML = "Field is not defined"
        return 1;
    }
    else{
        document.getElementById(error_id).innerHTML = ""
        return 0;
    }
};


/*
Function to hide input menu div when button is clicked
*/
$(function(data){
    var coll = document.getElementsByClassName("collapsible");
    coll[0].addEventListener("click", function(){
        console.log(coll[0].innerHTML)
        if(coll[0].innerHTML == '<i class="fa fa-toggle-up"></i>'){
            coll[0].innerHTML = '<i class="fa fa-toggle-down"></i>';
            document.getElementById('manhole-menu').classList.add("hideDiv");
        }
        else{
            coll[0].innerHTML = '<i class="fa fa-toggle-up"></i>';
            document.getElementById('manhole-menu').classList.remove("hideDiv");
        }
    });
});

/*
Function to retrieve map, retrieve map size, and hide map on page load
*/
$(function(data) { //wait for the page to load
    console.log("PAGE LOADED")
    ol_map = TETHYS_MAP_VIEW.getMap();
    previous_size = ol_map.getSize(); // Retrieve map size
    document.getElementById("manhole_map").classList.add("hideDiv"); // Hide ol map
});

$("#submit-manhole").click(process_manhole);

$(function(){

    $('#manhole-shp-upload-input').change(function(){
        uploadFile('#manhole-shp-upload-input', 'manhole_file', ".shp", 1);
    });

    $('#mhstreet-shp-upload-input').change(function(){
        uploadFile('#mhstreet-shp-upload-input', 'mhstreet_file', ".shp", 1);
    });

    $('#depth-shp-upload-input').change(function(){
        uploadFileNoFields('#depth-shp-upload-input', 'depth_file');
    });

});


