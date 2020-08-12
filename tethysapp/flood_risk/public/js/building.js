var building_risk;
var line_file;
var buffer;
var buildingid_field;
var tax_field;
var taxid_field;
var distance;

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

$(function(data) { //wait for the page to load
    console.log("PAGE LOADED")
    ol_map = TETHYS_MAP_VIEW.getMap();
    console.log(ol_map)
});

$(function(data){
    var coll = document.getElementsByClassName("collapsible");
    coll[0].addEventListener("click", function(){
        this.classList.toggle("active")
        var this_content = document.getElementById('building-menu')
        if(this_content.style.display === "block") {
            this_content.style.display = "none";
            coll[0].innerHTML = "+Show Inputs"
        } else {
            this_content.style.display = "block";
            coll[0].innerHTML = "-Hide Inputs"
        }
    });
});

$("#submit-buildings").click(process_buildings);

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


});


