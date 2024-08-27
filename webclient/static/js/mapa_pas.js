var global_map_can_edit = true;
var point_global_WGS84 = [0, 0];
var point_global_JTSK = [0, 0];
var lock = false;
var GLOBAL_DEBUG_TEXT=false;

var global_map_can_load_projects=true //zkontroluj
var boundsLock=false //zkontroluj

var poi_sugest= L.layerGroup();
var mcg = L.markerClusterGroup({ disableClusteringAtZoom: 20 }).addTo(map);
var poi_sn = L.featureGroup.subGroup(mcg)
var poi_pian = L.featureGroup.subGroup(mcg)
var heatPoints = [];
var heatmapOptions = settings_heatmap_options;
var heatLayer = new HeatmapOverlay( heatmapOptions);

map.addLayer(poi_sugest);

var overlays = {
    [map_translations['cuzkKatastralniMapa']]: cuzkWMS,
    [map_translations['cuzkKatastralniUzemi']]: cuzkWMS2,
    [map_translations['npuPamatkovaOchrana']]: npuOchrana,
    [map_translations['FindLocation']]:poi_sugest,
    [map_translations['samostatneNalezy']]: poi_sn,
    [map_translations['pian']]:poi_pian,
};

global_map_layers.remove(map);//remove previous overlay
L.control.layers(baseLayers, overlays).addTo(map);

var mem={
    "visible_x1":0.0,
    "visible_x2":0.0
}
map.on('click', function (e) {
    //if(('{{context.archivovano}}' === 'undefined' || '{{context.archivovano}}'=='False')){
    if (!global_measuring_toolbox._measuring) {
        if (global_map_can_edit) {
            if (!lock) {
                if (map.getZoom() > 15) {
                    point_global_WGS84= amcr_static_coordinate_precision_wgs84([e.latlng.lng, e.latlng.lat]);
                    point_global_JTSK = amcr_static_coordinate_precision_jtsk(convertToJTSK(point_global_WGS84[0], point_global_WGS84[1]));
                    point_leaf= [...point_global_WGS84].reverse();
                    if (document.getElementById('visible_ss_combo').value == 1) {
                        document.getElementById('visible_x1').value = point_global_WGS84[0];
                        document.getElementById('visible_x2').value = point_global_WGS84[1];
                    }
                    else if (document.getElementById('visible_ss_combo').value == 3) {
                        document.getElementById('visible_x1').value = degToDmsString(point_global_WGS84[0]);
                        document.getElementById('visible_x2').value = degToDmsString(point_global_WGS84[1]);
                    }
                    else if (document.getElementById('visible_ss_combo').value == 2) {
                        document.getElementById('visible_x1').value = -1*Math.abs(point_global_JTSK[0]);
                        document.getElementById('visible_x2').value = -1*Math.abs(point_global_JTSK[1]);
                    }
                    replace_coor();
                    document.getElementById('id_coordinate_wgs84_x1').value = point_global_WGS84[0]
                    document.getElementById('id_coordinate_wgs84_x2').value = point_global_WGS84[1]
                    document.getElementById('id_coordinate_sjtsk_x1').value = point_global_JTSK[0]
                    document.getElementById('id_coordinate_sjtsk_x2').value = point_global_JTSK[1]
                    addUniquePointToPoiLayer(point_leaf, '', false, true)
                    fill_katastr();
                } else {
                    map.setView(e.latlng, map.getZoom() + 2)
                }
            }
        }
    }
});

map.on('overlayadd', function(eventlayer){
    debugText("pridat mapu")
    if(eventlayer.layer===poi_pian || eventlayer.layer===poi_sn){
        switchMap(false)
    }
});

map.on('overlayremove', function(eventlayer){
    debugText("ubrat mapu")
    if(eventlayer.layer===poi_pian || eventlayer.layer===poi_sn){
        switchMap(false)
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

function onMarkerClick(ident_cely,e) {
    var popup = e.target.getPopup();
    popup.setContent("");
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/pian/mapa-connections/'+ident_cely);
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    }
    xhr.send();
    xhr.onload = function () {
        rs = JSON.parse(this.responseText).points
        text=""
        rs.forEach((i) => {
            let link='<a href="/id/' + i.dj + '" target="_blank">' + i.dj + '</a></br>'
            text=text+link
        })
        popup.setContent(text);
        
    }
 }

var debugText=(text)=>{
    if(GLOBAL_DEBUG_TEXT){
        console.log(text);
    }
}

var replace_coor = () => {
    dm=""
    if (document.getElementById('visible_ss_combo').value == 2) {
        dm="-"
    }
    var dx1='visible_x1';
    var dx2='visible_x2';
    if(document.getElementById(dx1).value.length>1){
        document.getElementById(dx1).value=(dm+document.getElementById(dx1).value.replace(".",",")).replace("--","-");
        document.getElementById(dx2).value=(dm+document.getElementById(dx2).value.replace(".",",")).replace("--","-");
        mem[dx1]=document.getElementById(dx1).value;
        mem[dx2]=document.getElementById(dx2).value;
    }
}

var fill_katastr = () => {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/pas/mapa-zjisti-katastr');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    } else {
        console.log("neni X-CSRFToken token")
    }
    xhr.onload = function () {
        debugText(this.responseText)
        rs = JSON.parse(this.responseText)
        if (rs.katastr_name) {
            document.getElementById("id_katastr").value = rs.katastr_name
        }
    };
    xhr.send(JSON.stringify(
        {
            'x2': parseFloat(point_global_WGS84[1]),
            'x1': parseFloat(point_global_WGS84[0]),
        }))
};


var is_in_czech_republic = (x1, x2) => {
    if (document.getElementById('visible_ss_combo').value == 1) {
        if (x1 >= 12.2401111182 && x1 <= 18.8531441586 && x2 >= 48.5553052842 && x2 <= 51.1172677679) {
            disableSaveButton(false)
            return true;
        } else {
            debugText("Coordinates not inside CR");
            disableSaveButton(true)
            //alert("Zadané souřadnice nejsou v ČR 1")
            point_global_WGS84 = [0, 0];
            poi_sugest.clearLayers();
            return false
        }
    } 
    else if (document.getElementById('visible_ss_combo').value == 3) {
        x1m=dmsStringToDeg(x1);
        x2m=dmsStringToDeg(x2);
        if (x1m >= 12.2401111182 && x1m <= 18.8531441586 && x2m >= 48.5553052842 && x2m <= 51.1172677679) {
            disableSaveButton(false)
            return true;
        } else {
            debugText("Coordinates not inside CR");
            disableSaveButton(true)
            //alert("Zadané souřadnice nejsou v ČR 1")
            point_global_WGS84 = [0, 0];
            poi_sugest.clearLayers();
            return false
        }
    } 
    else {
        if (x1 >= -889110.16 && x1 <= -448599.79 && x2 >= -1231915.96 && x2 <= -892235.44) {
            disableSaveButton(false)
            return true
        } else {
            debugText("Coordinates not inside CR 2");
            disableSaveButton(true)
            //alert("Zadané souřadnice nejsou v ČR")
            point_global_WGS84 = [0, 0];
            poi_sugest.clearLayers();
            return false;
        }
    }
};

let disableSaveButton=(dis)=>{
    if(document.getElementById('submit-id-save')){
        document.getElementById('submit-id-save').disabled=dis;
    }

}

let set_numeric_coordinates = async (push=false,addComa=false) => {
    debugText("switch set_numeric_coordinates");
    cor_x1 = document.getElementById('visible_x1').value.replace(",",".");
    cor_x2 = document.getElementById('visible_x2').value.replace(",",".");
    if (cor_x1!="" && is_in_czech_republic(cor_x1, cor_x2)) {
        if (document.getElementById('visible_ss_combo').value == 1) {
            point_global_WGS84 = amcr_static_coordinate_precision_wgs84([cor_x1, cor_x2]);
            point_global_JTSK = amcr_static_coordinate_precision_jtsk(convertToJTSK(cor_x1, cor_x2), false);
        }
        else if (document.getElementById('visible_ss_combo').value == 3) {
            cor_x1=dmsStringToDeg(cor_x1);
            cor_x2=dmsStringToDeg(cor_x2);
            point_global_WGS84 = amcr_static_coordinate_precision_wgs84([cor_x1, cor_x2]);
            point_global_JTSK = amcr_static_coordinate_precision_jtsk(convertToJTSK(cor_x1, cor_x2), false);
        }
        else if (document.getElementById('visible_ss_combo').value == 2) {
            point_global_JTSK = amcr_static_coordinate_precision_jtsk([cor_x1, cor_x2], false)
            point_global_WGS84 = amcr_static_coordinate_precision_wgs84(convertToWGS84(cor_x1, cor_x2));
        }
        point_leaf=[point_global_WGS84[1],point_global_WGS84[0]]
        addUniquePointToPoiLayer(point_leaf,"");
        fill_katastr();
        document.getElementById('id_coordinate_wgs84_x1').value = point_global_WGS84[0]
        document.getElementById('id_coordinate_wgs84_x2').value = point_global_WGS84[1]
        document.getElementById('id_coordinate_sjtsk_x1').value = point_global_JTSK[0]
        document.getElementById('id_coordinate_sjtsk_x2').value = point_global_JTSK[1]
        return true;
    }
    return false;
};

var switch_coordinate_system = () => {
    new_system = document.getElementById('visible_ss_combo').value
    switch_coor_system(new_system)
    replace_coor();
};

var dmsStringToDeg = (dmsString) => {
    if (dmsString.search('°')==-1)
        return parseFloat(dmsString);
    const dmsRegex = /(\d+)°\s*(\d+)?'?\s*([\d.,]+)?"?/;
    const matches = dmsString.match(dmsRegex);
    
    if (!matches) {
        throw new Error('Neplatný formát DMS');
    }
    
    const degrees = parseFloat(matches[1]);  // Stupně jsou vždy povinné
    const minutes = matches[2] ? parseFloat(matches[2]) : 0;  // Pokud nejsou zadané minuty, použijeme 0
    const seconds = matches[3] ? parseFloat(matches[3].replace(',', '.')) : 0;  // Pokud nejsou zadané sekundy, použijeme 0

    // Převod na desetinné stupně
    const decimalDegrees = degrees + (minutes / 60) + (seconds / 3600);
    return decimalDegrees;
}

var degToDmsString = (deg) => {
    const degrees = Math.floor(deg);
    const minutesFull = (deg - degrees) * 60;
    const minutes = Math.floor(minutesFull);
    const seconds = (minutesFull - minutes) * 60;

    // Formátování do řetězce
    return `${degrees}°${minutes}'${seconds.toFixed(4)}"`;
}

var switch_coor_system = (new_system) => {
    debugText("switch system: " + new_system)
     
    if (new_system == 1 ) {
        document.getElementById('id_coordinate_system').value="4326";
        if(point_global_WGS84[0] != 0){
            document.getElementById('visible_x1').value = point_global_WGS84[0]
            document.getElementById('visible_x2').value = point_global_WGS84[1]
            document.getElementById('visible_x1').readOnly = false;
            document.getElementById('visible_x2').readOnly = false;
       
        }
    }
    else if (new_system == 3 ) {
        document.getElementById('id_coordinate_system').value="4326";
        if(point_global_WGS84[0] != 0){
            document.getElementById('visible_x1').value = degToDmsString(point_global_WGS84[0])
            document.getElementById('visible_x2').value = degToDmsString(point_global_WGS84[1])
            document.getElementById('visible_x1').readOnly = false;
            document.getElementById('visible_x2').readOnly = false;
        
        }
    } 
    else if (new_system == 2) {
        document.getElementById('id_coordinate_system').value="5514";   
         if (point_global_JTSK[0] != 0) { 
            if(Math.abs(point_global_JTSK[0])<3000000){
                document.getElementById('visible_x1').value = -1*Math.abs(point_global_JTSK[0]);
                document.getElementById('visible_x2').value = -1*Math.abs(point_global_JTSK[1]);
            }
            document.getElementById('visible_x1').readOnly = false;
            document.getElementById('visible_x2').readOnly = false;  
        }
    }
};

const addUniquePointToPoiLayer = (point_leaf, text, zoom = true, redPin = false) => {
    var point_rec_leaf = amcr_static_coordinate_precision_wgs84(point_leaf);
    poi_sugest.clearLayers()
    if(redPin){
        L.marker(point_rec_leaf,{icon:pinIconRedPin, zIndexOffset: 2000})
        .bindTooltip(text)
        .bindPopup(text)
        .addTo(poi_sugest);
    } else {
        L.marker(point_rec_leaf,{icon:pinIconYellowPin, zIndexOffset: 2000})
        .bindTooltip(text)
        .bindPopup(text)
        .addTo(poi_sugest);
    }
    if (point_rec_leaf[0] && point_rec_leaf[1] && zoom) {
        map.setView(point_rec_leaf, 15);
    }

    if (point_global_WGS84[0] == 0) {
        jtsk_coor = amcr_static_coordinate_precision_jtsk(convertToJTSK(point_rec_leaf[0], point_rec_leaf[1]),true);
        point_global_WGS84 = [point_rec_leaf[0], point_rec_leaf[1]];
        point_global_JTSK = jtsk_coor;

    }
};

var addReadOnlyUniquePointToPoiLayer = (lat, long, ident_cely) => {
    addUniquePointToPoiLayer([lat, long], ident_cely, true)
    lock = false;
};

function showPosition(position) {
    var [latitude, longitude] = amcr_static_coordinate_precision_wgs84([position.coords.latitude, position.coords.longitude]);
    var latlng = new L.LatLng(latitude, longitude);

    map.setView(latlng, 16);
    addUniquePointToPoiLayer([latitude, longitude], '', false, true)

    point_global_WGS84 = [longitude,latitude];
    point_global_JTSK = amcr_static_coordinate_precision_jtsk(convertToJTSK(point_global_WGS84[0], point_global_WGS84[1]));
    if (document.getElementById('visible_ss_combo').value == 1) {
        document.getElementById('visible_x1').value = point_global_WGS84[0]
        document.getElementById('visible_x2').value = point_global_WGS84[1]
    }
    else if (document.getElementById('visible_ss_combo').value == 3) {
        document.getElementById('visible_x1').value = degToDmsString(point_global_WGS84[0]);
        document.getElementById('visible_x2').value = degToDmsString(point_global_WGS84[1]);
    }
    else if (document.getElementById('visible_ss_combo').value == 2) {
        document.getElementById('visible_x1').value = -1*Math.abs(point_global_JTSK[0])
        document.getElementById('visible_x2').value = -1*Math.abs(point_global_JTSK[1])
    }
    replace_coor();

    L.marker(latlng,{icon:pinIconGreenPin}).addTo(poi_sugest)
        .bindPopup("Vaše současná poloha")
        .openPopup();
};

$(document).ready(function () {
    debugText(document.getElementById('id_coordinate_system').value)
    my_wgs84_x1 = document.getElementById('id_coordinate_wgs84_x1').value;
    my_wgs84_x2 = document.getElementById('id_coordinate_wgs84_x2').value;
    my_sjtsk_x1 = document.getElementById('id_coordinate_sjtsk_x1').value;
    my_sjtsk_x2 = document.getElementById('id_coordinate_sjtsk_x2').value;
    my_sys = document.getElementById('id_coordinate_system').value;
    point_global_WGS84 = amcr_static_coordinate_precision_wgs84([my_wgs84_x1,my_wgs84_x2]);
    point_global_JTSK= amcr_static_coordinate_precision_jtsk([my_sjtsk_x1,my_sjtsk_x2]);

    if(point_global_JTSK[0]==0){
        point_global_JTSK = amcr_static_coordinate_precision_jtsk(convertToJTSK(point_global_WGS84[0],point_global_WGS84[1]))
    }
    if(my_wgs84_x1){
        point_leaf= [...point_global_WGS84].reverse();
        if(global_map_can_edit){
            addUniquePointToPoiLayer(point_leaf, map_translations.lokalizacePAS)
        } else {
            global_map_can_edit=false
            addReadOnlyUniquePointToPoiLayer(point_leaf)
        }
    }

    if(my_sys=="S-JTSK"  || my_sys=="S-JTSK*" || my_sys=='5514'){
        document.getElementById('visible_ss_combo').value = 2
    }
    else {
        document.getElementById('visible_ss_combo').value = 1
    }

})
var addPointToPoiLayer = (st_text, layer, text, overview = false, presnost) => {
    //addLogText("arch_z_detail_map.addPointToPoiLayer")
    let coor = []
    let myIco = { icon: pinIconPurplePoint };
    let myIco2 = { icon: pinIconPurpleHW };
    let myColor = { color: "rgb(151, 0, 156)" };
    if(presnost==4){
        myIco = { icon: pinIconPurpleHW};
    }

    if (st_text.includes("POLYGON") && presnost!=4) {
        st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0].replace("(", "")]))
        })
        L.polygon(coor, myColor)
        .bindTooltip(text+' ('+presnost+')', { sticky: true })
        .bindPopup("").on("click",onMarkerClick.bind(null,text))
        .addTo(layer);
    } else if (st_text.includes("LINESTRING")) {
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]))
        })
        L.polyline(coor, myColor)
        .bindTooltip(text+' ('+presnost+')', { sticky: true })
        .bindPopup("").on("click",onMarkerClick.bind(null,text))
        .addTo(layer);
    } else if (st_text.includes("POINT")) {
        let i = st_text.split("(")[1].split(")")[0];
        coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]))

    }
    if (overview && coor.length > 0) {
        x0 = 0.0;
        x1 = 0.0
        c0 = 0
        debugText(coor)
        for (const i of coor) {
            if(!(st_text.includes("POLYGON") && c0==coor.length-1)){
                x0 = x0 + parseFloat(i[0])
                x1 = x1 + parseFloat(i[1])
                c0 = c0 + 1
            }
        }
        if (st_text.includes("POLYGON") || st_text.includes("LINESTRING")) {
            L.marker(amcr_static_coordinate_precision_wgs84([x0 / c0, x1 / c0]), myIco2)
            .bindTooltip(text+' ('+presnost+')', { sticky: true })
            .bindPopup("").on("click",onMarkerClick.bind(null,text))
            .addTo(layer);
        } else {
            L.marker(amcr_static_coordinate_precision_wgs84([x0 / c0, x1 / c0]), myIco)
            .bindTooltip(text+' ('+presnost+')', { sticky: true })
            .bindPopup("").on("click",onMarkerClick.bind(null,text))
            .addTo(layer);
        }
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
            debugText("Change: " + northWest + "  " + southEast + " " + zoom);
            boundsLock = bounds;
            let xhr = new XMLHttpRequest();
            xhr.open('POST', '/mapa-pian-pas');
            xhr.setRequestHeader('Content-type', 'application/json');
            if (typeof global_csrftoken !== 'undefined') {
                xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
            }
            map.spin(false);
            map.spin(true);
            xhr.send(JSON.stringify(
                {
                    'northWest': northWest,
                    'southEast': southEast,
                    'zoom': zoom,
                    'pian':map.hasLayer(poi_pian),
                    'pas':map.hasLayer(poi_sn),
                }));

            xhr.onload = function () {
                try{
                    poi_sn.clearLayers();
                    poi_pian.clearLayers();
                    map.removeLayer(heatLayer);
                    let resAl = JSON.parse(this.responseText).algorithm
                    if (resAl == "detail") {
                        let resPoints = JSON.parse(this.responseText).points
                        resPoints.forEach((i) => {

                            if(i.type=="pas"){
                                let ge = i.geom.split("(")[1].split(")")[0];
                                L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconPurplePin })
                                .bindTooltip(i.ident_cely, { sticky: true })
                                .bindPopup('<a href="/pas/detail/'+i.ident_cely+'" target="_blank">'+i.ident_cely+'</a>')
                                .addTo(poi_sn)
                            } else if(i.type=="pian"){
                                addPointToPoiLayer(i.geom, poi_pian, i.ident_cely, true,i.presnost)
                            }
                        })
                    } else {
                        heatPoints=[]
                        let resHeat = JSON.parse(this.responseText).heat
                        let maxHeat=0;
                        resHeat.forEach((i) => {
                            geom = i.geom.split("(")[1].split(")")[0].split(" ");
                            if(i.pocet>maxHeat){
                                maxHeat=i.pocet;
                            }
                                //from: {"id": "1", "pocet": 32, "density": 0, "geom": "POINT(14.8 50.120000000000005)"}
                                //to: {lat: 24.6408, lng:46.7728, count: 3}
                            heatPoints.push({lat:parseFloat(geom[1]), lng:parseFloat(geom[0]), count:i.pocet});//chyba je to geome
                        })
                        heatLayer = new HeatmapOverlay( heatmapOptions); //= L.heatLayer(heatPoints, heatmapOptions);
                        debugText({max:maxHeat,data:heatPoints})
                        heatLayer.setData({max:maxHeat,data:heatPoints})
                        map.addLayer(heatLayer);
                        //poi_other.clearLayers();
                        //poi_other_dp.clearLayers();
                        //poi_dj.clearLayers();
                    }
                    map.spin(false);
                } catch(e){map.spin(false);debugText(e)}
            };
        }
    }
}
