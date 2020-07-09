var building_risk;
var line_file;
var buffer;
var objectid_field;
var tax_field;
var taxid_field;


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


upload_building_file = function(){
    var shapefiles = $("#shp-upload-input")[0].files;

    //Preparing data to be submitted via AJAX POST request
    var data = new FormData();
    buffer = document.getElementById("buffer-input").value;
    data.append("buffer", buffer);

    for (var i=0; i<shapefiles.length; i++){
        data.append("shapefile", shapefiles[i]);
    }

    var submit_button = $("#submit-building");
    var submit_button_html = submit_button.html();
    submit_button.text('Submitting...');

    building_risk(data);

};

building_risk = function(data) {
    var bldg_risk = ajax_update_database_with_file("building-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.

    bldg_risk.done(function(return_data){ //Reset the form once the data is added successfully
        if("field_names" in return_data){
            var submit_button = $("#submit-building");
            var submit_button_html = submit_button.html();
            submit_button.text('Submitted');
            var options = return_data.field_names;

            var select = document.getElementById("objectid-field")

            // Optional: Clear all existing options first:
            select.innerHTML="<option value=\""+"Select Bldg OBJECTID Field"+"\">" +"Select Bldg OBJECTID Field"+"</option>";
            // Populate list with options:
            for(var i=0; i<options.length; i++){
                var opt = options[i];
                select.innerHTML += "<option value=\"" + opt + "\">" + opt + "</option>";
            }
        };
    });
}

upload_tax_file = function(){
    var shapefiles = $("#tax-upload-input")[0].files;

    //Preparing data to be submitted via AJAX POST request
    var data = new FormData();

    for (var i=0; i<shapefiles.length; i++){
        data.append("shapefile", shapefiles[i]);
    }

    var submit_button = $("#submit-tax");
    var submit_button_html = submit_button.html();
    submit_button.text('Submitting...');

    tax_risk(data);
};

tax_risk = function(data) {
    var tax_file = ajax_update_database_with_file("tax-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.

    tax_file.done(function(return_data){ //Reset the form once the data is added successfully
        if("tax_names" in return_data){
            var submit_button = $("#submit-tax");
            var submit_button_html = submit_button.html();
            submit_button.text('Submitted');
            var options = return_data.tax_names;

            var select = document.getElementById("tax-field")

            // Optional: Clear all existing options first:
            select.innerHTML="<option value=\""+"Select Tax Parcel Field"+"\">" +"Select Tax Parcel Field"+"</option>";
            // Populate list with options:
            for(var i=0; i<options.length; i++){
                var opt = options[i];
                select.innerHTML += "<option value=\"" + opt + "\">" + opt + "</option>";
            }

            select = document.getElementById("taxid-field")

            // Optional: Clear all existing options first:
            select.innerHTML="<option value=\""+"Select Tax OBJECTID Field"+"\">" +"Select Tax OBJECTID Field"+"</option>";
            // Populate list with options:
            for(var i=0; i<options.length; i++){
                var opt = options[i];
                select.innerHTML += "<option value=\"" + opt + "\">" + opt + "</option>";
            }
        };
    });
}

process_tax = function(data) {
    tax_field = document.getElementById("tax-field").value;
    taxid_field = document.getElementById("taxid-field").value;

    var data = new FormData();
    data.append("tax_field", tax_field)
    data.append("taxid_field", taxid_field)

    var submit_button = $("#submit-process-tax");
    var submit_button_html = submit_button.html();
    submit_button.text('Submitted');

    var process_tax_file = ajax_update_database_with_file("tax-process2-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
}

upload_land_file = function(){
    var shapefiles = $("#land-upload-input")[0].files;

    //Preparing data to be submitted via AJAX POST request
    var data = new FormData();

    for (var i=0; i<shapefiles.length; i++){
        data.append("shapefile", shapefiles[i]);
    }

    var submit_button = $("#submit-land");
    var submit_button_html = submit_button.html();
    submit_button.text('Submitting...');

    land_risk(data);
};

land_risk = function(data) {
    var land_file = ajax_update_database_with_file("land-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.

    land_file.done(function(return_data){ //Reset the form once the data is added successfully
        if("land_names" in return_data){
            var submit_button = $("#submit-land");
            var submit_button_html = submit_button.html();
            submit_button.text('Submitted');
            var options = return_data.land_names;

            var select = document.getElementById("land-field")

            // Optional: Clear all existing options first:
            select.innerHTML="<option value=\""+"Select Landuse Field"+"\">" +"Select Landuse Field"+"</option>";
            // Populate list with options:
            for(var i=0; i<options.length; i++){
                var opt = options[i];
                select.innerHTML += "<option value=\"" + opt + "\">" + opt + "</option>";
            }

            var select = document.getElementById("landid-field")

            // Optional: Clear all existing options first:
            select.innerHTML="<option value=\""+"Select Landuse ID Field"+"\">" +"Select Landuse ID Field"+"</option>";
            // Populate list with options:
            for(var i=0; i<options.length; i++){
                var opt = options[i];
                select.innerHTML += "<option value=\"" + opt + "\">" + opt + "</option>";
            }
        };
    });
}

process_land = function(data) {
    land_field = document.getElementById("land-field").value;
    landid_field = document.getElementById("landid-field").value;

    var data = new FormData();
    data.append("land_field", land_field)
    data.append("landid_field", landid_field)

    var submit_button = $("#submit-process-land");
    var submit_button_html = submit_button.html();
    submit_button.text('Submitted');

    var process_tax_file = ajax_update_database_with_file("land-process2-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
}

raster_file = function(data) {
    objectid_field = document.getElementById("objectid-field").value;
    var rasters = $("#raster-upload-input")[0].files;
    var data = new FormData();
    for(var i=0; i< rasters.length; i++){
        data.append("raster", rasters[i]);
    }
    data.append("objectid_field", objectid_field)
    var depth_raster = ajax_update_database_with_file("raster-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.

}

$("#submit-building").click(upload_building_file);
$("#submit-tax").click(upload_tax_file);
$("#submit-process-tax").click(process_tax);
$("#submit-land").click(upload_land_file);
$("#submit-process-land").click(process_land);
$("#submit-depth").click(raster_file);


