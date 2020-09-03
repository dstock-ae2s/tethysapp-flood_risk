var buffer;
var distance;
var street_buffer;
var streetid_field;
var pipe_rad;
var street_rad;

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


function process_pipe(){

    var data = new FormData();

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

    sum_check = (check(pipeid_field, "pipe-field-select-0-error")+check(slope, "pipe-field-select-1-error")
                +check(diameter, "pipe-field-select-2-error")+check(flow, "pipe-field-select-3-error")
                +check(streetid_field, "street2-field-select-0-error")+check(street_flow, "street2-field-select-1-error")
                +check(street_buffer, "street2-buffer-error")+check(pipe_buffer, "pipe-buffer-error")
                +check(distance, "street2-distance-error"))
    if(sum_check==0){
        var pipe_risk = ajax_update_database_with_file("pipe-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
        map_bounds = pipe_risk["bounds"]
    }
}

hide_field = function(id_field){
    x = document.getElementById(id_field);
    x.style.display = "none";
}

show_field = function(id_field){
    x = document.getElementById(id_field);
    x.style.display = "inline-block";
}

$(function(data) { //wait for the page to load
    ol_map = TETHYS_MAP_VIEW.getMap();
    console.log(ol_map)
});

$(function(data){
    var coll = document.getElementsByClassName("collapsible");
    coll[0].addEventListener("click", function(){
        this.classList.toggle("active")
        var this_content = document.getElementById('pipe-menu')
        if(this_content.style.display === "block") {
            this_content.style.display = "none";
            coll[0].innerHTML = "+Show Inputs"
        } else {
            this_content.style.display = "block";
            coll[0].innerHTML = "-Hide Inputs"
        }
    });
});

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
}

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


