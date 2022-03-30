var global_map_can_edit = true;
var point_global_WGS84 = [0, 0];
var point_global_JTSK = [0, 0];
var lock = false;

map.on('click', function (e) {
    //if(('{{context.archivovano}}' === 'undefined' || '{{context.archivovano}}'=='False')){
    if (!global_measuring_toolbox._measuring) {
        if (global_map_can_edit) {
            if (!lock) {
                if (map.getZoom() > 15) {
                    var [corX, corY] = amcr_static_coordinate_precision_wgs84([e.latlng.lat, e.latlng.lng]);
                    jtsk_coor = amcr_static_coordinate_precision_jtsk(convertToJTSK(corX, corY));
                    //point_global_WGS84 = [Math.round(corX * 1000000) / 1000000, Math.round(corY * 1000000) / 1000000]
                    point_global_WGS84 = [corX, corY];
                    //point_global_JTSK = [-Math.round(jtsk_coor[0] * 100) / 100, -Math.round(jtsk_coor[1] * 100) / 100]
                    point_global_JTSK = jtsk_coor
                    if (document.getElementById('detector_system_coordinates').value == 1) {
                        document.getElementById('detector_coordinates_x').value = point_global_WGS84[0]
                        document.getElementById('detector_coordinates_y').value = point_global_WGS84[1]
                    } else if (document.getElementById('detector_system_coordinates').value == 2) {
                        document.getElementById('detector_coordinates_x').value = point_global_JTSK[0]
                        document.getElementById('detector_coordinates_y').value = point_global_JTSK[1]
                    }
                    $("#detector_coordinates_x").change();
                    $("#detector_coordinates_y").change();
                    console.log("lll "+corX+"  "+corY)
                    addUniquePointToPoiLayer(corX, corY, '', false, true)
                    fill_katastr();
                } else {
                    map.setView(e.latlng, map.getZoom() + 2)
                }
            }
        }
    }
});


var fill_katastr = () => {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/pas/pas-zjisti-katastr');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    } else {
        console.log("neni X-CSRFToken token")
    }
    xhr.onload = function () {
        console.log(this.responseText)
        rs = JSON.parse(this.responseText)
        if (rs.katastr_name) {
            document.getElementById("id_katastr").value = rs.katastr_name
        }
    };
    xhr.send(JSON.stringify(
        {
            'cX': parseFloat(point_global_WGS84[1]),
            'cY': parseFloat(point_global_WGS84[0]),
        }))
};

var is_in_czech_republic = (corX, corY) => {
    console.log("Test coordinates for bounding box");

    if (document.getElementById('detector_system_coordinates').value == 1) {
        if (corY >= 12.2401111182 && corY <= 18.8531441586 && corX >= 48.5553052842 && corX <= 51.1172677679) {

            return true;
        } else {
            console.log("Coordinates not inside CR");
            point_global_WGS84 = [0, 0];
            poi.clearLayers();
            return false
        }
    } else {
        if (corX >= -889110.16 && corX <= -448599.79 && corY >= -1231915.96 && corY <= -892235.44) {
            return true
        } else {
            console.log("Coordinates not inside CR");
            point_global_WGS84 = [0, 0];
            poi.clearLayers();
            return false;
        }
    }
};

let set_numeric_coordinates = async () => {
    corX = document.getElementById('detector_coordinates_x').value;
    corY = document.getElementById('detector_coordinates_y').value;
    console.log(corX+" . "+corY)
    if (is_in_czech_republic(corX, corY)) {
        if (document.getElementById('detector_system_coordinates').value == 1) {
            jtsk_coor = convertToJTSK(corX, corY);
            point_global_WGS84 = amcr_static_coordinate_precision_wgs84([corX, corY]);
            point_global_JTSK = amcr_static_coordinate_precision_jtsk(jtsk_coor, true);
            addUniquePointToPoiLayer(corX, corY);
            //point_global_WGS84 = [Math.round(corX * 1000000) / 1000000, Math.round(corY * 1000000) / 1000000]
            //point_global_JTSK = [-Math.round(jtsk_coor[0] * 100) / 100, -Math.round(jtsk_coor[1] * 100) / 100]
            //addUniquePointToPoiLayer($("#detector_coordinates_x").val(), $("#detector_coordinates_y").val())
            fill_katastr();
            return true;
        } else if (document.getElementById('detector_system_coordinates').value == 2) {
            $.getJSON("https://epsg.io/trans?x=" + (corX).toFixed(2) + "&y=" + (corY).toFixed(2) + "&s_srs=5514&t_srs=4326", async function (data) {
                //point_global_WGS84 = [Math.round(data.y * 1000000.0) / 1000000.0, Math.round(data.x * 1000000.0) / 1000000.0]
                //point_global_JTSK = [Math.round(corX * 100.0) / 100.0, Math.round(corY * 100.0) / 100.0]
                point_global_WGS84 = amcr_static_coordinate_precision_wgs84([data.y, data.x])
                point_global_JTSK = amcr_static_coordinate_precision_jtsk([corX, corY], false)
                addUniquePointToPoiLayer(point_global_WGS84[0], point_global_WGS84[1])
                fill_katastr();
                return true;
            })
        }
    }
    return false;
};

var switch_coordinate_system = () => {
    new_system = document.getElementById('detector_system_coordinates').value
    switch_coor_system(new_system)
};

var switch_coor_system = (new_system) => {
    console.log("switch system: " + new_system)
    if (new_system == 1 && point_global_WGS84[0] != 0) {
        document.getElementById('detector_coordinates_x').value = point_global_WGS84[0]
        document.getElementById('detector_coordinates_y').value = point_global_WGS84[1]
        document.getElementById('detector_coordinates_x').readOnly = false;
        document.getElementById('detector_coordinates_y').readOnly = false;
    } else if (new_system == 2 && point_global_JTSK[0] != 0) {
        document.getElementById('detector_coordinates_x').value = point_global_JTSK[0]
        document.getElementById('detector_coordinates_y').value = point_global_JTSK[1]
        document.getElementById('detector_coordinates_x').readOnly = false;
        document.getElementById('detector_coordinates_y').readOnly = false;
    }
};

//var addPointToPoiLayer = (lat, long, text) => {
//    L.marker([lat, long]).bindPopup(text).addTo(poi);
//};
var addUniquePointToPoiLayer = (lat, long, text, zoom = true, redPin = false) => {
    var [corX, corY] = amcr_static_coordinate_precision_wgs84([lat, long]);
    poi.clearLayers()
    if(redPin){
        L.marker([corX, corY],{icon:pinIconRedPin}).bindPopup("Vámi vyznačená poloha").addTo(poi);
    } else {
        L.marker([corX, corY],{icon:pinIconGreenPin}).bindPopup("Vámi vyznačená poloha").addTo(poi);
    }
    if (corX && corY && zoom) {
        map.setView([corX, corY], 15);
    }

    if (point_global_WGS84[0] == 0) {
        jtsk_coor = amcr_static_coordinate_precision_jtsk(convertToJTSK(corX, corY),true);
        point_global_WGS84 = [corX, corY];
        point_global_JTSK = jtsk_coor;
        //point_global_WGS84 = [Math.round(lat * 1000000) / 1000000, Math.round(long * 1000000) / 1000000]
        //point_global_JTSK = [-Math.round(jtsk_coor[0] * 100) / 100, -Math.round(jtsk_coor[1] * 100) / 100]

    }
};

var addReadOnlyUniquePointToPoiLayer = (lat, long, text) => {
    addUniquePointToPoiLayer(lat, long, text, true)
    lock = false;
};

function showPosition(position) {
    var [latitude, longitude] = amcr_static_coordinate_precision_wgs84([position.coords.latitude, position.coords.longitude]);
    var latlng = new L.LatLng(latitude, longitude);

    map.setView(latlng, 16);
    addUniquePointToPoiLayer(latitude, longitude, '', false, true)

    document.getElementById('detector_system_coordinates').value = 1
    point_global_WGS84 = [latitude, longitude];
    //point_global_WGS84 = [Math.round(latitude * 1000000) / 1000000, Math.round(longitude * 1000000) / 1000000]
    document.getElementById('detector_coordinates_x').value = point_global_WGS84[0]
    document.getElementById('detector_coordinates_y').value = point_global_WGS84[1]

    L.marker(latlng,{icon:pinIconGreenPin}).addTo(poi)
        .bindPopup("Vaše současná poloha")
        .openPopup();
};
