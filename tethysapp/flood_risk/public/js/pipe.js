/*
Declaring global variables
*/
var buffer; //Buffer around pipes to pull max depth from
var distance; //Road segment length
var street_buffer; //Buffer around streets to pull max depth from
var streetid_field; //ID of street from input shapefile
var pipe_rad; //Value of radio button
var street_rad; //Value of radio button

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
Function which extracts flood depths around streets from raster
and associates this value with a pipes shapefile then calculates
necessary pipe diameter to contain pipe and street flow
*/
function process_pipe(){

    var data = new FormData();
    console.log("In process pipe")

    // Read in input values
    pipeid_field = document.getElementById("pipe-field-select-0").value;
    data.append("pipeid_field", pipeid_field)

    slope = document.getElementById("pipe-field-select-1").value;
    data.append("slope", slope);

    diameter = document.getElementById("pipe-field-select-2").value;
    data.append("diameter", diameter);

    flow = document.getElementById("pipe-field-select-3").value;
    data.append("flow", flow);

    streetid_field = document.getElementById("street2-field-select-0").value;
    data.append("streetid_field", streetid_field);

    street_flow = document.getElementById("street2-field-select-1").value;
    data.append("street_flow", street_flow);

    street_buffer = document.getElementById("street2-buffer").value;
    data.append("street_buffer", street_buffer);

    pipe_buffer = document.getElementById("pipe-buffer").value;
    data.append("pipe_buffer", pipe_buffer);

    distance = document.getElementById("street2-distance").value;
    data.append("distance", distance);

    mannings_n = 0.013
    data.append("mannings_n", mannings_n)

    pipe_rad = document.forms[0].elements.pipe_radio.value;
    data.append("pipe_rad", pipe_rad)

    street_rad = document.forms[0].elements.street_radio.value;
    data.append("street_rad", street_rad)

    // Check for errors from input values
    var pipe_check;
    var street_check;
    var street_flow_check;
    if(pipe_rad=="no"){
        pipe_check = 0;
    } else{
        pipe_check = check(flow, "pipe-field-select-3-error");
    }
    if(street_rad=="no"){
        street_check = 0;
        street_flow_check = check(street_flow, "street2-field-select-1-error");
    } else{
        street_check = check(street_buffer, "street2-buffer-error");
        street_flow_check = 0;
    }
    sum_check = (check(pipeid_field, "pipe-field-select-0-error")+check(slope, "pipe-field-select-1-error")
                +check(diameter, "pipe-field-select-2-error")+pipe_check
                +check(streetid_field, "street2-field-select-0-error")+street_flow_check
                +street_check+check(pipe_buffer, "pipe-buffer-error")
                +check(distance, "street2-distance-error"))
    console.log(sum_check)
    if(sum_check==0){
        // Call ajax function
        var pipe_risk = ajax_update_database_with_file("pipe-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
        pipe_risk.done(function(return_data){
            console.log("Pipe risk done")

            ol_map = TETHYS_MAP_VIEW.getMap();
            document.getElementById("pipe_map").classList.remove("hideDiv"); // Show the map
            ol_map.setSize(previous_size); // Resize the map to fit the div
            ol_map.renderSync(); // Update the map
            (document.getElementsByClassName("collapsible"))[0].click(); // Collapse input menu div

            // Style pipes layer
            var styles = [
                new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: '#A9A9A9',
                        width: 6,
                        zIndex: 0
                    })
                }),
                new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: '#FFD300',
                        width: 5,
                        zIndex: 1
                    })
                })
            ];

            // Create a geojson object holding pipe features
            var geojson_object = {
                'type': 'FeatureCollection',
                'crs': {
                    'type': 'name',
                    'properties': {
                        'name': 'EPSG:3857'
                    }
                },
                'features': return_data.pipes_features
            };

            // Convert from geojson to openlayers collection
            var these_features = new ol.format.GeoJSON().readFeatures(geojson_object);

            // Create a new ol source and assign pipe features
            var vectorSource = new ol.source.Vector({
                features: these_features
            });

            // Create a new modifiable layer and assign source and style
            var pipeLayer = new ol.layer.Vector({
                name: 'Pipes',
                source: vectorSource,
                style: styles,
            });

            // Add pipes layer to map
            ol_map = TETHYS_MAP_VIEW.getMap();
            ol_map.addLayer(pipeLayer);
            ol_map = TETHYS_MAP_VIEW.getMap();

            // Define a new legend
            var legend = new ol.control.Legend({
                title: 'Legend',
                margin: 5,
                collapsed: false
            });
            ol_map.addControl(legend);
            legend.addRow({
                title: 'Pipes',
                typeGeom:'Point',
                style: new ol.style.Style({
                    image: new ol.style.RegularShape({
                        points: 4,
                        radius: 10,
                        angle: Math.PI / 4,
                        stroke: new ol.style.Stroke({ color: '#A9A9A9', width: 2 }),
                        fill: new ol.style.Fill({ color: '#FFD300'})
                    })
                })
            });
            TETHYS_MAP_VIEW.zoomToExtent(return_data.extent) // Zoom to layer
        });
    }
}

/*
Function which hides inputs based on radio button
*/
hide_field = function(id_field){
    x = document.getElementById(id_field);
    x.style.display = "none";
}

/*
Function which shows inputs based on radio button
*/
show_field = function(id_field){
    x = document.getElementById(id_field);
    x.style.display = "inline-block";
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
            document.getElementById('pipe-menu').classList.add("hideDiv");
        }
        else{
            coll[0].innerHTML = '<i class="fa fa-toggle-up"></i>';
            document.getElementById('pipe-menu').classList.remove("hideDiv");
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
    document.getElementById("pipe_map").classList.add("hideDiv"); // Hide ol map
});


$("#submit-pipe").click(process_pipe);

$(function(){

    $('#depth2-shp-upload-input').change(function(){
        uploadFileNoFields('#depth2-shp-upload-input', 'depth2_file');
    });

    $('#pipe-shp-upload-input').change(function(){
        uploadFile('#pipe-shp-upload-input', 'pipe_file', ".shp", 4);
    });

    $('#street2-shp-upload-input').change(function(){
        uploadFile('#street2-shp-upload-input', 'street2_file', ".shp", 2);
    });

    if(document.forms[0].elements.street_radio.value == "yes"){
        hide_field('street2-field-select-1-group');
        show_field('depth2-raster');
        show_field('street2-buffer-group');
    }
    $(document.forms[0].elements.street_radio).change(function(){
        if(document.forms[0].elements.street_radio.value == "yes"){
        hide_field('street2-field-select-1-group');
        show_field('depth2-raster');
        show_field('street2-buffer-group');
        } else {
        show_field('street2-field-select-1-group');
        hide_field('depth2-raster');
        hide_field('street2-buffer-group');
        };
    });

    if(document.forms[0].elements.pipe_radio.value == "no"){
        hide_field('pipe-field-select-3-group');
    }
    $(document.forms[0].elements.pipe_radio).change(function(){
        if(document.forms[0].elements.pipe_radio.value == "yes"){
        show_field('pipe-field-select-3-group');
        } else {
        hide_field('pipe-field-select-3-group');
        };
    });

});


