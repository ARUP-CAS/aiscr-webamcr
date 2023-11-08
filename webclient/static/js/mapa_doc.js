var global_map_can_edit = true;
var point_global_WGS84 = [0, 0];
var point_global_JTSK = [0, 0];
var lock = false;
var global_map_can_load_projects=true
var boundsLock=false

var poi_model= L.layerGroup();
var poi_all = L.markerClusterGroup({ disableClusteringAtZoom: 20 })

map.addLayer(poi_model);

var overlays = {
    "ČÚZK - Katastrální mapa": cuzkWMS,
    "ČÚZK - Katastrální území": cuzkWMS2,
    "Lokalizace modelu":poi_model,
    "Knihovna 3D":poi_all,
};
global_map_layers.remove(map);//remove previous overlay
L.control.layers(baseLayers, overlays).addTo(map);

map.on('click', function (e) {
    if (!global_measuring_toolbox._measuring) {
        let [corX, corY] = amcr_static_coordinate_precision_wgs84([e.latlng.lat, e.latlng.lng]);
        if (global_map_can_edit) {
            if (!lock) {
                point_global_WGS84 = [corX, corY];
                document.getElementById('id_coordinate_x').value = point_global_WGS84[0]
                document.getElementById('id_coordinate_y').value = point_global_WGS84[1]
                document.getElementById('id_sirka').value = point_global_WGS84[0]
                document.getElementById('id_vyska').value = point_global_WGS84[1]

                $("#vyska").change();
                $("#sirka").change();
                addUniquePointToPoiLayer(corX, corY, '', false, true)
                replace_coor();
            }
        }
    }
});

var is_in_czech_republic = (corX, corY) => {
    console.log("Test coordinates for bounding box");

    if (corY >= 12.2401111182 && corY <= 18.8531441586 && corX >= 48.5553052842 && corX <= 51.1172677679) {
        return true;
    } else {
        console.log("Coordinates not inside CR");
        point_global_WGS84 = [0, 0];
        poi_model.clearLayers();
        return false
    }
};


//var addPointToPoiLayer = (lat, long, text) => {
//    L.marker([lat, long]).bindPopup(text).addTo(poi);
//};
var addUniquePointToPoiLayer = (lat, long, text, zoom = true,redIcon= false) => {
    var [corX, corY] = amcr_static_coordinate_precision_wgs84([lat, long]);
    poi_model.clearLayers()
    if(redIcon){
        L.marker([corX, corY],{icon:pinIconRed3D, zIndexOffset: 2000}).bindPopup("Vámi vyznačená poloha").addTo(poi_model);
    }else{
        L.marker([corX, corY],{icon:pinIconYellow3D, zIndexOffset: 2000}).bindPopup("Vámi vyznačená poloha").addTo(poi_model);
    }

    if (corX && corY && zoom) {
        map.setView([corX, corY], 15);
    }
    point_global_WGS84 = [corX, corY];
}

var addReadOnlyUniquePointToPoiLayer = (corX, corY, text) => {
    addUniquePointToPoiLayer(corX, corY, text, true)
    lock = false;
};

//Get position - needed in GetLocation method
function showPosition(position) {
    var [latitude, longitude] = amcr_static_coordinate_precision_wgs84([position.coords.latitude, position.coords.longitude]);
    var latlng = new L.LatLng(latitude, longitude);

    map.setView(latlng, 16);
    addUniquePointToPoiLayer(latitude, longitude, '', false, true)

    point_global_WGS84 = [latitude, longitude];
    document.getElementById('id_coordinate_x').value = point_global_WGS84[0]
    document.getElementById('id_coordinate_y').value = point_global_WGS84[1]
    document.getElementById('id_sirka').value = point_global_WGS84[0]
    document.getElementById('id_vyska').value = point_global_WGS84[1]

    L.marker(latlng).addTo(poi_model)
        .bindPopup("Vaše současná poloha")
        .openPopup();
}


var replace_coor = () => {
    var dx='id_sirka';
    var dy='id_vyska';
    if(typeof InstallTrigger == 'undefined'){//!firefox
        document.getElementById(dx).value=(document.getElementById(dx).value);
        document.getElementById(dy).value=(document.getElementById(dy).value);
    }else{
        document.getElementById(dx).value=(document.getElementById(dx).value.replace(".",","));
        document.getElementById(dy).value=(document.getElementById(dy).value.replace(".",","));
    }
}

map.on('moveend', function () {
    switchMap(false);
});

switchMap = function (overview = false) {
    var bounds = map.getBounds();
    let zoom = map.getZoom();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();
    if (global_map_can_load_projects) {
        if (overview || bounds.northWest != boundsLock.northWest || !boundsLock.northWest) {
            console.log("Change: " + northWest + "  " + southEast + " " + zoom);
            boundsLock = bounds;
            let xhr_3d_all = new XMLHttpRequest();
            xhr_3d_all.open('POST', '/dokument/mapa-3d');
            xhr_3d_all.setRequestHeader('Content-type', 'application/json');
            if (typeof global_csrftoken !== 'undefined') {
                xhr_3d_all.setRequestHeader('X-CSRFToken', global_csrftoken);
            }
            map.spin(false);
            map.spin(true);
            xhr_3d_all.send(JSON.stringify(
                {
                    'northWest': northWest,
                    'southEast': southEast,
                    'zoom': zoom,
                }));

            xhr_3d_all.onload = function () {
                try{
                    poi_all.clearLayers(poi_all);
                    let resPoints = JSON.parse(this.responseText).points
                    resPoints.forEach((i) => {
                        let ge = i.geom.split("(")[1].split(")")[0];
                        L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconPurple3D }).bindPopup(i.ident_cely).addTo(poi_all)
                    })
                    map.spin(false);
                } catch(e){map.spin(false);}
            };
            xhr_3d_all.onerror = function () {
                map.spin(false);
            };
        }
    }
}
