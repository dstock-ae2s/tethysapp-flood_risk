
var buffer;
var manholeid_field;
var map_bounds;
var ol_layer;
var extent;


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

process_manhole = function(data) {

    var data = new FormData();

    manholeid_field = document.getElementById("manhole-field-select-0").value;
    data.append("manholeid_field", manholeid_field)

    street_depth = document.getElementById("mhstreet-field-select-0").value;
    data.append("street_depth", street_depth)

    buffer = document.getElementById("manhole-buffer").value;
    data.append("buffer", buffer);

    sum_check = (check(buffer, "manhole-buffer-error")
                +check(manholeid_field, "manhole-field-select-0-error")
                +check(street_depth, "mhstreet-field-select-0-error"))


    if(sum_check == 0){
        var manhole_risk = ajax_update_database_with_file("manhole-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
            manhole_risk.done(function(return_data){
                if("extent" in return_data){
                    if(document.readyState == 'complete'){
                        centroid = return_data.centroid;
                        extent = return_data.extent;
                        document.getElementById("manhole-hidden-extent").innerHTML = extent;
                        document.getElementById("manhole-hidden-centroid").innerHTML = centroid;
                        ol_map = TETHYS_MAP_VIEW.getMap();
                        ol_map.getLayers().forEach(layer => layer.getSource().refresh());
                        TETHYS_MAP_VIEW.zoomToExtent(extent);
                        //if(document.readyState=='complete'){
                           // ol_map = TETHYS_MAP_VIEW.getMap();
                            //ol_layer = MVLayer(
                             //   source='ImageWMS',
                             //   options={
                              //     'url': 'http://localhost:8080/geoserver/wms',
                              //     'params': {'LAYERS': 'flood-risk:MH_Street_Inundation'},
                               //    'serverType': 'geoserver'
                               // },
                               // legend_title=""
                           // )

                         //   if (return_data.geoserver_layer){
                              //  ol_layer = new ol.layer.Image({
                              //      extent: return_data.extent,
                              //      source: new ol.source.ImageWMS({
                              //          url: 'http://localhost:8080/geoserver/wms',
                             //           params: {'LAYERS': 'flood-risk:MH_Street_Inundation'},
                             //           ratio: 1,
                              //          serverType: 'geoserver',
                             //       }),
                             //   });
                           //     console.log("OL LAYER")
                             //   console.log(ol_layer)
                             //   ol_map.addLayer(ol_layer);
                            //}
                        //}
                    }

                }
            });
    }
}

$(function(data) { //wait for the page to load
    console.log("PAGE LOADED")
    ol_map = TETHYS_MAP_VIEW.getMap();
    console.log(ol_map)
});

$(function(data){
    var coll = document.getElementsByClassName("collapsible");
    coll[0].addEventListener("click", function(){
        this.classList.toggle("active")
        var this_content = document.getElementById('manhole-menu')
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
};


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


