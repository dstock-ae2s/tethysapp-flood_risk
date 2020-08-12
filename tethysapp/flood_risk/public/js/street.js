
var buffer;
var distance;
var street_buffer;
var streetid_field;

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

$(function(data) { //wait for the page to load
    console.log("PAGE LOADED")
    ol_map = TETHYS_MAP_VIEW.getMap();
    console.log(ol_map)
});


$(function(data){
    var coll = document.getElementsByClassName("collapsible");
    coll[0].addEventListener("click", function(){
        this.classList.toggle("active")
        var this_content = document.getElementById('street-menu')
        if(this_content.style.display === "block") {
            this_content.style.display = "none";
            coll[0].innerHTML = "+Show Inputs"
        } else {
            this_content.style.display = "block";
            coll[0].innerHTML = "-Hide Inputs"
        }
    });
});

$("#submit-streets").click(process_streets);

$(function(){

    $('#street-shp-upload-input').change(function(){
        uploadFile('#street-shp-upload-input', 'street_file', ".shp", 1);
    });

});


