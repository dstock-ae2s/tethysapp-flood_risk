
var buffer;
var distance;
var street_buffer;
var streetid_field;
var previous_target;
var previous_viewport;
var previous_size;

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

process_streets = function(data) {

    var data = new FormData();

    streetid_field = document.getElementById("street-field-select-0").value;
    data.append("streetid_field", streetid_field)

    buffer = document.getElementById("street-buffer").value;
    data.append("buffer", buffer);

    distance = document.getElementById("distance-input").value;
    data.append("distance", distance);

    sum_check = (check(buffer, "street-buffer-error")
                +check(streetid_field, "street-field-select-0-error")
                +check(distance, "distance-input-error"))
    if(sum_check == 0){
        var street_risk = ajax_update_database_with_file("streets-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
        street_risk.done(function(return_data){
            console.log("PREVIOUS TARGET")
            console.log(previous_target);
            ol_map = TETHYS_MAP_VIEW.getMap();
//            changeTheTarget(previous_target, ol_map);
            document.getElementById("street_map").classList.remove("hideDiv");
            ol_map.setSize(previous_size);
            ol_map.renderSync();

            console.log(ol_map.getViewport());
            console.log(ol_map.getSize());
            console.log(ol_map.getView());
            var styles = {
                'Point': new ol.style.Style({
                    image: new ol.style.Circle({
                        radius: 20,
                        fill: null,
                        stroke: new ol.style.Stroke({color: 'red', width: 1}),
                    }),
                }),
                'LineString': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'green',
                        width: 20,
                    }),
                }),
                'GeometryCollection': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'magenta',
                        width: 20,
                    }),
                    fill: new ol.style.Fill({
                        color: 'magenta',
                    }),
                    image: new ol.style.Circle({
                        radius: 20,
                        fill: null,
                        stroke: new ol.style.Stroke({
                            color: 'magenta',
                        }),
                    }),
                }),
                'Circle': new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'red',
                        width: 20,
                    }),
                    fill: new ol.style.Fill({
                        color: 'rgba(255,0,0,0.2)',
                    }),
                }),
            };
            var styleFunction = function(feature) {
                return styles[feature.getGeometry().getType()];
            };
//            geojson_style =  new ol.style.Style({
//                stroke: new ol.style.Stroke({
//                    color: 'red',
//                    width: 20
//                }),
//                fill: new ol.style.Fill({
//                    color: 'green'
//                }),
//                image: new ol.style.Circle({
//                    radius: 10,
//                    fill: new ol.style.Fill({
//                        color: 'red'
//                    }),
//                    stroke: new ol.style.Stroke({
//                        color: 'red',
//                        width: 2
//                    })
//                })
//            });
//
            var geojson_object = {
                'type': 'FeatureCollection',
                'crs': {
                    'type': 'name',
                    'properties': {
                        'name': 'EPSG:3857'
                    }
                },
                'features': return_data.streets_features
            };

//            var geojson_object = {
//                'type': 'FeatureCollection',
//                'crs': {
//                    'type': 'name',
//                    'properties': {
//                        'name': 'EPSG:4326',
//                    },
//                },
//                'features': [
//                {
//                    'type': 'Feature',
//                    'geometry': {
//                        'type': 'LineString',
//                        'coordinates': [
//                            [35.15625, 18.31281],
//                            [73.125, -18.64624] ],
//                    },
//                } ],
//            };

            console.log(return_data.streets_features)
            console.log(geojson_object)

//            var vectorSource = new ol.source.Vector({
//                features: new ol.format.GeoJSON().readFeatures(geojson_object),
//            });

            var vectorSource = new ol.source.Vector({
                features: new ol.format.GeoJSON().readFeatures(geojson_object)
            });

            vectorSource.addFeature(new ol.Feature(new ol.geom.Circle([5e6, 7e6], 1e6)));
//            vectorSource.addFeature(new ol.Feature(new ol.geom.LineString([[4e6, 2e6], [8e6,-2e6]])));

            console.log("After features")

//            var streetLayer = new ol.layer.Vector({
//                title: 'Streets',
//                source: vectorSource,
//                style: styleFunction,
//            });

            var streetLayer = new ol.layer.Vector({
                title: 'Streets',
                source: vectorSource,
                style: styleFunction,
            });

            console.log("After layer")
            console.log(streetLayer)

//            geojson_layer = MVLayer(
//                source='GeoJSON',
//                options=geojson_object,
//                layer_options={'style': style},
//                legend_title='Test GeoJSON',
//                legend_extent=[-46.7, -48.5, 74, 59],
//                legend_classes=[
//                    MVLegendClass('line', 'Lines', stroke='red')
//                ],
//            );
            ol_map = TETHYS_MAP_VIEW.getMap();
            ol_map.addLayer(streetLayer);
            TETHYS_MAP_VIEW.updateLegend();

//            $(function(){
//                ol_map = TETHYS_MAP_VIEW.getMap();
//                ol_map.addLayer(streetLayer);
//                TETHYS_MAP_VIEW.updateLegend();
//                ol_map.setSize(previous_size);
//                ol_map.renderSync();
//            });
            TETHYS_MAP_VIEW.zoomToExtent(return_data.extent)
        });
    };
};

function changeTheTarget(previousTarget, ol_map){
    ol_map.setTarget(previousTarget);
    console.log("FIN")
}

$(function(data) { //wait for the page to load
    console.log("PAGE LOADED")
    ol_map = TETHYS_MAP_VIEW.getMap();
    previous_target = ol_map.getTargetElement();
    previous_size = ol_map.getSize();
    console.log(ol_map.getViewport());
    console.log(ol_map.getSize());
    console.log(ol_map.getView());
    previous_viewport = ol_map.getViewport();
//    document.getElementById("street_map").classList.add("hideDiv");
//    ol_map.setTarget(null);
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

$("#submit-streets").click(process_streets);

$(function(){

    $('#street-shp-upload-input').change(function(){
        uploadFile('#street-shp-upload-input', 'street_file', ".shp", 1);
    });
    $('#depth-shp-upload-input').change(function(){
        uploadFileNoFields('#depth-shp-upload-input', 'depth_file');
    });

});


