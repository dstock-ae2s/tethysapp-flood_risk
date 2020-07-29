var building_risk;
var line_file;
var buffer;
var buildingid_field;
var tax_field;
var taxid_field;
var distance;
var street_buffer;
var streetid_field;


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


//find if method is csrf safe
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

//add csrf token to appropriate ajax requests
$(function() {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            }
        }
    });
}); //document ready


function addErrorMessage(error, div_id) {
    var div_id_string = '#message';
    if (typeof div_id != 'undefined') {
        div_id_string = '#'+div_id;
    }
    $(div_id_string).html(
      '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>' +
      '<span class="sr-only">Error:</span> ' + error
    )
    .removeClass('hidden')
    .removeClass('alert-success')
    .removeClass('alert-info')
    .removeClass('alert-warning')
    .addClass('alert')
    .addClass('alert-danger');

}
//Add success message when stuff gets done successfully
function addSuccessMessage(message, div_id) {
    var div_id_string = '#message';
    if (typeof div_id != 'undefined') {
        div_id_string = '#'+div_id;
    }
    $(div_id_string).html(
      '<span class="glyphicon glyphicon-ok-circle" aria-hidden="true"></span>' +
      '<span class="sr-only">Sucess:</span> ' + message
    ).removeClass('hidden')
    .removeClass('alert-danger')
    .removeClass('alert-info')
    .removeClass('alert-warning')
    .addClass('alert')
    .addClass('alert-success');
}

//send data to database but follow this if you have files assosciated with it.
function ajax_update_database_with_file(ajax_url, ajax_data,div_id) {
    //backslash at end of url is required
    if (ajax_url.substr(-1) !== "/") {
        ajax_url = ajax_url.concat("/");
    }

    //update database
    var xhr = jQuery.ajax({
        url: ajax_url,
        type: "POST",
        data: ajax_data,
        dataType: "json",
        processData: false, // Don't process the files
        contentType: false // Set content type to false as jQuery will tell the server its a query string request
    });
    xhr.done(function(data) {
        //if("success" in data){
            //addSuccessMessage(data['success'],div_id);
        //}else{
            //appendErrorMessage(data['error'],div_id);
        //}
    })
    .fail(function(xhr, status, error) {

        console.log(xhr.responseText);

    });
    return xhr;
}

function hideShowFieldDivs(div_id){
    if(document.getElementById(div_id).style.display == "none"){
        document.getElementById(div_id).style.display == "block";
    }
};

function checkNumberOfFields(dropdown_id, div_id){
    var num_fields = $('#'+dropdown_id).val();
    for(var i = 1, l = 2; i <= l; ++i){
        document.getElementById(div_id+i).style.display = "none";
    }
    for(var i = 1, l = num_fields; i <= l; ++i){
        hideShowFieldDivs(div_id + i);
    }
};

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


process_buildings = function(){
    var data = new FormData();

    buffer = document.getElementById("buffer-input").value;
    data.append("buffer", buffer);

    buildingid_field = document.getElementById("bldg-field-select-0").value;
    data.append("buildingid_field", buildingid_field);

    taxid_field = document.getElementById("tax-field-select-0").value;
    data.append("taxid_field", taxid_field);

    tax_field = document.getElementById("tax-field-select-1").value;
    data.append("tax_field", tax_field);

    landuseid_field = document.getElementById("landuse-field-select-0").value;
    data.append("landuseid_field", landuseid_field);

    landuse_field = document.getElementById("landuse-field-select-1").value;
    data.append("landuse_field", landuse_field);

    var bldg_risk = ajax_update_database_with_file("building-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.

};

process_streets = function(data) {

    var data = new FormData();

    streetid_field = document.getElementById("street-field-select-0").value;
    data.append("streetid_field", streetid_field)

    buffer = document.getElementById("street-buffer").value;
    data.append("buffer", buffer);

    distance = document.getElementById("distance-input").value;
    data.append("distance", distance);

    var street_risk = ajax_update_database_with_file("streets-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
};

process_manhole = function(data) {

    var data = new FormData();

    manholeid_field = document.getElementById("manhole-field-select-0").value;
    data.append("manholeid_field", manholeid_field)

    buffer = document.getElementById("manhole-buffer").value;
    data.append("buffer", buffer);

    var manhole_risk = ajax_update_database_with_file("manhole-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
}

process_pipe = function(data) {

    var data = new FormData();

    pipeid_field = document.getElementById("pipe-field-select-0").value;
    data.append("pipeid_field", pipeid_field)

    flow = document.getElementById("pipe-field-select-1").value;
    data.append("flow", flow);

    diameter = document.getElementById("pipe-field-select-2").value;
    data.append("diameter", diameter);

    slope = document.getElementById("pipe-field-select-3").value;
    data.append("slope", slope);

    streetid_field = document.getElementById("street2-field-select-0").value;
    data.append("streetid_field", streetid_field);

    street_flow = document.getElementById("street2-field-select-1").value;
    data.append("street_flow", street_flow);

    buffer = document.getElementById("street2-buffer").value;
    data.append("buffer", buffer);

    distance = document.getElementById("street2-distance").value;
    data.append("distance", distance);

    mannings_n = 0.013
    data.append("mannings_n", mannings_n)

    var pipe_risk = ajax_update_database_with_file("pipe-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
}

$("#submit-buildings").click(process_buildings);
$("#submit-streets").click(process_streets);
$("#submit-manhole").click(process_manhole);
$("#submit-pipe").click(process_pipe);

$(function(){

    $('#bldg-shp-upload-input').change(function(){
        uploadFile('#bldg-shp-upload-input', 'bldg_file', ".shp", 1);
    });

    $('#depth-shp-upload-input').change(function(){
        uploadFileNoFields('#depth-shp-upload-input', 'depth_file');
    });

    $('#tax-shp-upload-input').change(function(){
        uploadFile('#tax-shp-upload-input', 'tax_file', ".shp", 2);
    });

    $('#landuse-shp-upload-input').change(function(){
        uploadFile('#landuse-shp-upload-input', 'landuse_file', ".shp", 2);
    });

    $('#street-shp-upload-input').change(function(){
        uploadFile('#street-shp-upload-input', 'street_file', ".shp", 1);
    });

    $('#manhole-shp-upload-input').change(function(){
        uploadFile('#manhole-shp-upload-input', 'manhole_file', ".shp", 1);
    });

    $('#pipe-shp-upload-input').change(function(){
        uploadFile('#pipe-shp-upload-input', 'pipe_file', ".shp", 4);
    });

    $('#street2-shp-upload-input').change(function(){
        uploadFile('#street2-shp-upload-input', 'street2_file', ".shp", 2);
    });

});


