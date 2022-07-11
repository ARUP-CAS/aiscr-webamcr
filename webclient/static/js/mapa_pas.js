var global_map_can_edit = true;
var point_global_WGS84 = [0, 0];
var point_global_JTSK = [0, 0];
var lock = false;

var mem={
    "detector_coordinates_x":0.0,
    "detector_coordinates_y":0.0
}
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
                        document.getElementById('detector_coordinates_x').value = -1*Math.abs(point_global_JTSK[0])
                        document.getElementById('detector_coordinates_y').value = -1*Math.abs(point_global_JTSK[1])
                    }
                    replace_coor();
                    document.getElementById('id_coordinate_wgs84_x').value = point_global_WGS84[0]
                    document.getElementById('id_coordinate_wgs84_y').value = point_global_WGS84[1]
                    document.getElementById('id_coordinate_sjtsk_x').value = point_global_JTSK[0]
                    document.getElementById('id_coordinate_sjtsk_y').value = point_global_JTSK[1]
                    addUniquePointToPoiLayer(corX, corY, '', false, true)
                    fill_katastr();
                } else {
                    map.setView(e.latlng, map.getZoom() + 2)
                }
            }
        }
    }
});

var replace_coor = () => {
    dm=""
    if (document.getElementById('detector_system_coordinates').value == 2) {
        dm="-"
    }
    var dx='detector_coordinates_x';
    var dy='detector_coordinates_y';
    document.getElementById(dx).value=(dm+document.getElementById(dx).value.replace(".",",")).replace("--","-");
    document.getElementById(dy).value=(dm+document.getElementById(dy).value.replace(".",",")).replace("--","-");
    mem[dx]=document.getElementById(dx).value;
    mem[dy]=document.getElementById(dy).value;
}

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


var transformSinglePoint = async(y_plus,x_plus,push) => {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/transformace-single-wgs84');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    } else {
        console.log("neni X-CSRFToken token")
    }
    xhr.onload = function () {
        rs = JSON.parse(this.responseText)
        point_global_WGS84 = amcr_static_coordinate_precision_wgs84([rs.cx,rs.cy])
        addUniquePointToPoiLayer(point_global_WGS84[0], point_global_WGS84[1])
        fill_katastr();
        document.getElementById('id_coordinate_wgs84_x').value = point_global_WGS84[0]
        document.getElementById('id_coordinate_wgs84_y').value = point_global_WGS84[1]
        document.getElementById('id_coordinate_sjtsk_x').value = point_global_JTSK[0]
        document.getElementById('id_coordinate_sjtsk_y').value = point_global_JTSK[1]
        if(push){
            document.getElementById('detector_coordinates_x').value = point_global_JTSK[0]
            document.getElementById('detector_coordinates_y').value = point_global_JTSK[1]
            switch_coordinate_system();
        }

    };
    xhr.send(JSON.stringify({"cy" : y_plus, "cx" : x_plus}))
};

    /*var ipoints=[]
    ipoints.push([646760.290, 1060814.217])
    ipoints.push([646860.290, 1050814.217])
    ipoints.push([646960.290, 1040814.217])
    ipoints.push([647960.290, 1040814.217])
    transformMultiPoins(ipoints)*/

var transformMultiPoins = async(ipoints) => {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/transformace-multi-wgs84');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    } else {
        console.log("neni X-CSRFToken token")
    }
    xhr.onload = function () {
        rs = JSON.parse(this.responseText)
        console.log(rs)

    };
    xhr.send(JSON.stringify({"points" : ipoints}))
};

var is_in_czech_republic = (corX, corY) => {
    //console.log("Test coordinates for bounding box: "+corX+" "+corY);

    if (document.getElementById('detector_system_coordinates').value == 1) {
        if (corY >= 12.2401111182 && corY <= 18.8531441586 && corX >= 48.5553052842 && corX <= 51.1172677679) {
            disableSaveButton(false)
            return true;
        } else {
            console.log("Coordinates not inside CR");
            disableSaveButton(true)
            //alert("Zadané souřadnice nejsou v ČR 1")
            point_global_WGS84 = [0, 0];
            poi.clearLayers();
            return false
        }
    } else {
        if (corX >= -889110.16 && corX <= -448599.79 && corY >= -1231915.96 && corY <= -892235.44) {
            disableSaveButton(false)
            return true
        } else {
            console.log("Coordinates not inside CR 2");
            disableSaveButton(true)
            //alert("Zadané souřadnice nejsou v ČR")
            point_global_WGS84 = [0, 0];
            poi.clearLayers();
            return false;
        }
    }
};


let disableSaveButton=(dis)=>{
    if(document.getElementById('submit-id-save')){
        document.getElementById('submit-id-save').disabled=dis;
    }

}

let set_numeric_coordinates = async (push=false) => {
    corX = document.getElementById('detector_coordinates_x').value.replace(",",".");
    corY = document.getElementById('detector_coordinates_y').value.replace(",",".");
    if(Math.sign(corX) == Math.sign(corY) && document.getElementById('detector_system_coordinates').value == 2){
        corX=-1.0*Math.abs(corX);
        corY=-1.0*Math.abs(corY);
    }
    //console.log(corX+" . "+corY)
    if (corX!="" && is_in_czech_republic(corX, corY)) {
        if (document.getElementById('detector_system_coordinates').value == 1) {
            jtsk_coor = convertToJTSK(corX, corY);
            point_global_WGS84 = amcr_static_coordinate_precision_wgs84([corX, corY]);
            point_global_JTSK = amcr_static_coordinate_precision_jtsk(jtsk_coor, true);
            addUniquePointToPoiLayer(corX, corY);
            //point_global_WGS84 = [Math.round(corX * 1000000) / 1000000, Math.round(corY * 1000000) / 1000000]
            //point_global_JTSK = [-Math.round(jtsk_coor[0] * 100) / 100, -Math.round(jtsk_coor[1] * 100) / 100]
            //addUniquePointToPoiLayer($("#detector_coordinates_x").val(), $("#detector_coordinates_y").val())
            fill_katastr();
            document.getElementById('id_coordinate_wgs84_x').value = point_global_WGS84[0]
            document.getElementById('id_coordinate_wgs84_y').value = point_global_WGS84[1]
            document.getElementById('id_coordinate_sjtsk_x').value = point_global_JTSK[0]
            document.getElementById('id_coordinate_sjtsk_y').value = point_global_JTSK[1]
            if(push){
                document.getElementById('detector_coordinates_x').value = point_global_WGS84[0]
                document.getElementById('detector_coordinates_y').value = point_global_WGS84[1]
            }
            return true;
        } else if (document.getElementById('detector_system_coordinates').value == 2) {
            point_global_JTSK = amcr_static_coordinate_precision_jtsk([corX, corY], false)
            transformSinglePoint(Math.abs(Number(corX).toFixed(2)),Math.abs(Number(corY).toFixed(2)),true);//+y+x

        }
    }
    return false;
};

var switch_coordinate_system = () => {
    new_system = document.getElementById('detector_system_coordinates').value
    switch_coor_system(new_system)
    replace_coor();
};

var switch_coor_system = (new_system) => {
    console.log("switch system: " + new_system)
    if (new_system == 1 && point_global_WGS84[0] != 0) {
        document.getElementById('detector_coordinates_x').value = point_global_WGS84[0]
        document.getElementById('detector_coordinates_y').value = point_global_WGS84[1]
        document.getElementById('detector_coordinates_x').readOnly = false;
        document.getElementById('detector_coordinates_y').readOnly = false;
        document.getElementById('id_coordinate_system').value="wgs84";
    } else if (new_system == 2 && point_global_JTSK[0] != 0) {
        document.getElementById('detector_coordinates_x').value = -1*Math.abs(point_global_JTSK[0]);
        document.getElementById('detector_coordinates_y').value = -1*Math.abs(point_global_JTSK[1]);
        document.getElementById('detector_coordinates_x').readOnly = false;
        document.getElementById('detector_coordinates_y').readOnly = false;
        document.getElementById('id_coordinate_system').value="sjtsk";
    }
};

var addUniquePointToPoiLayer = (lat, long, text, zoom = true, redPin = false) => {
    var [corX, corY] = amcr_static_coordinate_precision_wgs84([lat, long]);
    poi.clearLayers()
    if(redPin){
        L.marker([corX, corY],{icon:pinIconRedPin}).bindPopup("Vámi vyznačená poloha").addTo(poi);
    } else {
        L.marker([corX, corY],{icon:pinIconYellowPin}).bindPopup("Vámi vyznačená poloha").addTo(poi);
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
    replace_coor();

    L.marker(latlng,{icon:pinIconGreenPin}).addTo(poi)
        .bindPopup("Vaše současná poloha")
        .openPopup();
};

$(document).ready(function () {
    my_wgs84_x = document.getElementById('id_coordinate_wgs84_x').value;
    my_wgs84_y = document.getElementById('id_coordinate_wgs84_y').value;
    my_sjtsk_x = document.getElementById('id_coordinate_sjtsk_x').value;
    my_sjtsk_y = document.getElementById('id_coordinate_sjtsk_y').value;
    my_sys = document.getElementById('id_coordinate_system').value;
    let [cor_wgs84_x, cor_wgs84_y] = amcr_static_coordinate_precision_wgs84([my_wgs84_x,my_wgs84_y]);
    let [cor_sjtsk_x, cor_sjtsk_y] = amcr_static_coordinate_precision_jtsk([my_sjtsk_x,my_sjtsk_y]);

    point_global_WGS84=[cor_wgs84_x, cor_wgs84_y];
    if(cor_sjtsk_x==0){
        point_global_JTSK = amcr_static_coordinate_precision_jtsk(convertToJTSK(point_global_WGS84[0],point_global_WGS84[1]))
    } else{
        point_global_JTSK =[cor_sjtsk_x, cor_sjtsk_y];
    }

    if(my_wgs84_x){
        if(global_map_can_edit){
            addUniquePointToPoiLayer(cor_wgs84_x, cor_wgs84_y)
        } else {
            global_map_can_edit=false
            addReadOnlyUniquePointToPoiLayer(cor_wgs84_x, cor_wgs84_y)
        }
    }

    if(my_sys=="S-JTSK"){
        console.log("prepnu na sjtsk")
        document.getElementById('detector_system_coordinates').value = 2
    }else {
        document.getElementById('detector_system_coordinates').value = 1
    }

})
