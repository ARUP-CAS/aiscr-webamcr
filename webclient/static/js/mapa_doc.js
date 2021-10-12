var global_map_can_edit = true;
var point_global_WGS84 = [0, 0];
var point_global_JTSK = [0, 0];
var lock = false;

map.on('click', function (e) {
    if(!global_measuring_toolbox._measuring){
        corX = e.latlng.lat;
        corY = e.latlng.lng;

        if(global_map_can_edit){
        if (!lock) {
            point_global_WGS84 = [Math.round(corX * 1000000) / 1000000, Math.round(corY * 1000000) / 1000000]
                document.getElementById('id_coordinate_x').value = point_global_WGS84[0]
                document.getElementById('id_coordinate_y').value = point_global_WGS84[1]
                document.getElementById('id_vyska').value = point_global_WGS84[0]
                document.getElementById('id_sirka').value = point_global_WGS84[1]

            $("#vyska").change();
            $("#sirka").change();
            addUniquePointToPoiLayer(corX, corY, '', false)
        }
        }
    }
});

var is_in_czech_republic = (corX,corY) => {
    console.log("Test coordinates for bounding box");

    if(corY>=12.2401111182 && corY<=18.8531441586 && corX>=48.5553052842 && corX<=51.1172677679){
        return true;
    }else {
        console.log("Coordinates not inside CR");
        point_global_WGS84 = [0, 0];
        poi.clearLayers();
        return false
    }
};


var addPointToPoiLayer = (lat, long, text) => {
    L.marker([lat, long]).bindPopup(text).addTo(poi);
};
var addUniquePointToPoiLayer = (lat, long, text, zoom = true) => {
    poi.clearLayers()
    L.marker([lat, long]).bindPopup("Vámi vyznačená poloha").addTo(poi);
    if (long && lat && zoom) {
        map.setView([lat, long], 15);
    }
    point_global_WGS84 = [Math.round(lat * 1000000) / 1000000, Math.round(long * 1000000) / 1000000]
}

var addReadOnlyUniquePointToPoiLayer = (lat, long, text) => {
    addUniquePointToPoiLayer(lat, long, text, true)
    lock = false;
};

//Get position - needed in GetLocation method
function showPosition(position) {
    var latitude = position.coords.latitude;
    var longitude = position.coords.longitude;
    var latlng = new L.LatLng(latitude, longitude);

    map.setView(latlng, 16);
    addUniquePointToPoiLayer(latitude, longitude, '', false)

    point_global_WGS84 = [Math.round(latitude * 1000000) / 1000000, Math.round(longitude * 1000000) / 1000000]
    document.getElementById('id_coordinate_x').value = point_global_WGS84[0]
    document.getElementById('id_coordinate_y').value = point_global_WGS84[1]
    document.getElementById('id_vyska').value = point_global_WGS84[0]
    document.getElementById('id_sirka').value = point_global_WGS84[1]

    L.marker(latlng).addTo(poi)
        .bindPopup("Vaše současná poloha")
        .openPopup();
};
