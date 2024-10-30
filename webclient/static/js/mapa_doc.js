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
    [map_translations['cuzkKatastralniMapa']]: cuzkWMS,
    [map_translations['cuzkKatastralniUzemi']]: cuzkWMS2,
    [map_translations['npuPamatkovaOchrana']]: npuOchrana,
    [map_translations['Location3D']]:poi_model,
    [map_translations['Library3D']]:poi_all,
};
global_map_layers.remove(map);//remove previous overlay
L.control.layers(baseLayers, overlays).addTo(map);

map.on('click', function (e) {
    if (!global_measuring_toolbox._measuring) {
        let point_leaf= amcr_static_coordinate_precision_wgs84([e.latlng.lat, e.latlng.lng]);
        if (global_map_can_edit) {
            if (!lock) {
                point_global_WGS84 = [...point_leaf].reverse();
                document.getElementById('id_visible_x1').value = point_global_WGS84[0] //visible
                document.getElementById('id_visible_x2').value = point_global_WGS84[1]
                document.getElementById('id_coordinate_wgs84_x1').value = point_global_WGS84[0] //hiden
                document.getElementById('id_coordinate_wgs84_x2').value = point_global_WGS84[1]

                $("#visible_x1").change();
                $("#visible_x2").change();
                addUniquePointToPoiLayer(point_leaf, '', false, true)
                replace_coor();
            }
        }
    }
});

map.on('popupclose', function (e) {

    // make the tooltip for this feature visible again
    // but check first, not all features will have tooltips!
    var tooltip = e.popup._source.getTooltip();
    if (tooltip) tooltip.setOpacity(0.9);

});

map.on('popupopen', function (e) {

    var tooltip = e.popup._source.getTooltip();
    // not all features will have tooltips!
    if (tooltip) 
    {
        // close the open tooltip, if you have configured animations on the tooltip this looks snazzy
        e.target.closeTooltip();
        // use opacity to make the tooltip for this feature invisible while the popup is active.
        e.popup._source.getTooltip().setOpacity(0);
    }

});

var is_in_czech_republic = (x2, x1) => {
    console.log("Test coordinates for bounding box");

    if (x1 >= 12.2401111182 && x1 <= 18.8531441586 && x2 >= 48.5553052842 && x2 <= 51.1172677679) {
        return true;
    } else {
        console.log("Coordinates not inside CR");
        point_global_WGS84 = [0, 0];
        poi_model.clearLayers();
        return false
    }
};

var addUniquePointToPoiLayer = (arg_point_leaf, ident_cely, zoom = true,redIcon= false) => {
    var point_leaf = amcr_static_coordinate_precision_wgs84(arg_point_leaf);
    poi_model.clearLayers()
    if(redIcon){
        L.marker(point_leaf,{icon:pinIconRed3D, zIndexOffset: 2000})
        .bindTooltip(ident_cely)
        .bindPopup(ident_cely)
        .addTo(poi_model);
    }else{
        L.marker(point_leaf,{icon:pinIconYellow3D, zIndexOffset: 2000})
        .bindTooltip(ident_cely)
        .bindPopup(ident_cely)
        .addTo(poi_model);
    }

    if (point_leaf[0] && point_leaf[1] && zoom) {
        map.setView(point_leaf, 9);
    }
    point_global_WGS84 = [...point_leaf].reverse()
}

var addReadOnlyUniquePointToPoiLayer = (point_leaf, ident_cely) => {
    addUniquePointToPoiLayer(point_leaf, ident_cely, true)
    lock = false;
};

//Get position - needed in GetLocation method
function showPosition(position) {
    var [latitude, longitude] = amcr_static_coordinate_precision_wgs84([position.coords.latitude, position.coords.longitude]);
    var latlng = new L.LatLng(latitude, longitude);

    map.setView(latlng, 10);
    addUniquePointToPoiLayer([latitude, longitude], '', false, true)

    point_global_WGS84 = [longitude, latitude];
    document.getElementById('id_visible_x1').value = point_global_WGS84[0] //visible
    document.getElementById('id_visible_x2').value = point_global_WGS84[1]
    document.getElementById('id_coordinate_wgs84_x1').value = point_global_WGS84[0] //hiden
    document.getElementById('id_coordinate_wgs84_x2').value = point_global_WGS84[1]

    L.marker(latlng).addTo(poi_model)
        .bindPopup([map_translations['CurrentLocation']]) // "Vaše současná poloha"
        .openPopup();
}


var replace_coor = () => {
    var x1='id_visible_x1';
    var x2='id_visible_x2';
    if(typeof InstallTrigger == 'undefined'){//!firefox
        document.getElementById(x1).value=(document.getElementById(x1).value);
        document.getElementById(x2).value=(document.getElementById(x2).value);
    }else{
        document.getElementById(x1).value=(document.getElementById(x1).value.replace(".",","));
        document.getElementById(x2).value=(document.getElementById(x2).value.replace(".",","));
    }
}

map.on('moveend', function () {
    switchMap(false);
});

$(document).ready(function () {
    switchMap(false);
})

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
            xhr_3d_all.open('POST', '/dokument/model/mapa-3d');
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
                        L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconPurple3D })
                        .bindTooltip(i.ident_cely, { sticky: true })
                        .bindPopup('<a href="/dokument/model/detail/'+i.ident_cely+'" target="_blank">'+i.ident_cely+'</a>')
                        .addTo(poi_all)
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
