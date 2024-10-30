var global_map_can_edit = true;
var global_map_can_load_projects = true;
var boundsLock = 0;
var ORIGIN_KATASTR = "";
var PROJEKT_IDENT_CELY= "";

var mcg = L.markerClusterGroup({ disableClusteringAtZoom: 20 }).addTo(map);
var poi_p1 = L.featureGroup.subGroup(mcg)
var poi_p2 = L.featureGroup.subGroup(mcg)
var poi_p3 = L.featureGroup.subGroup(mcg)
var poi_p46 = L.featureGroup.subGroup(mcg)
var poi_p78 = L.featureGroup.subGroup(mcg)
var poi_sugest = L.layerGroup();
var poi_correct = L.layerGroup();
var poi_sn = L.featureGroup.subGroup(mcg)
var poi_pian = L.featureGroup.subGroup(mcg)
map.addLayer(poi_sugest);
map.addLayer(poi_correct);
map.addLayer(poi_p1);
map.addLayer(poi_p2);
map.addLayer(poi_p3);
map.addLayer(poi_sn);
map.addLayer(poi_pian);

var heatPoints = [];
var heatmapOptions = settings_heatmap_options;
//var heatLayer = L.heatLayer(heatPoints, heatmapOptions);
heatLayer = new HeatmapOverlay( heatmapOptions)

var global_clusters = false;
var global_heat = false;

var overlays = {
    [map_translations['cuzkKatastralniMapa']]: cuzkWMS,
    [map_translations['cuzkKatastralniUzemi']]: cuzkWMS2,
    [map_translations['npuPamatkovaOchrana']]: npuOchrana,
    [map_translations['lokalizaceProjektu']]:poi_sugest,
    [map_translations['projektyP1']]:poi_p1,
    [map_translations['projektyP2']]:poi_p2,
    [map_translations['projektyP3']]:poi_p3,
    [map_translations['projektyP46']]:poi_p46,
    [map_translations['projektyP78']]:poi_p78,
    [map_translations['projektyPAS']]:poi_sn,
    [map_translations['projektyPIAN']]:poi_pian,
};

if (global_map_layers) {
    global_map_layers.remove(map);//remove previous overlay
}
var control = L.control.layers(baseLayers, overlays).addTo(map);

L.easyButton('bi bi-skip-backward-fill', function () {
    poi_correct.clearLayers();
    if (poi_sugest.getLayers().length>0) {
        let ll = poi_sugest.getLayers()[0]._latlng;
        map.setView(ll, 12);
        try {
            document.getElementById('id_coordinate_x2').value = ll.lat;
            document.getElementById('id_coordinate_x1').value = ll.lng;
        } catch (e) {
            console.log("Error: Element coordinate_x1/x2 doesn exists")
        }
        //Vratit puvodni katastr
        const select = $("input[name='hlavni_katastr']");
        if (global_map_can_edit && select && ORIGIN_KATASTR.length > 1) {
            select.val(ORIGIN_KATASTR);

        }
    } else {
        if(document.getElementById('id_coordinate_x2')!=null && document.getElementById('id_coordinate_x1')!=null ){
            document.getElementById('id_coordinate_x2').value = "";
            document.getElementById('id_coordinate_x1').value = "";
        }
        map.setView([50,15],1);

    }
}, [map_translations['DefaultTitle']]).addTo(map)


var button_map_lock = L.easyButton({
    states: [{
        stateName: 'add-lock',
        icon: 'bi bi-lock',
        title: [map_translations['EditTurnOff']],
        onClick: function (control) {
            global_map_can_edit = !global_map_can_edit;
            control.state('remove-lock');
        }
    }, {
        icon: 'bi bi-geo-alt',
        stateName: 'remove-lock',
        title: [map_translations['EditTurnOn']],
        onClick: function (control) {
            global_map_can_edit = !global_map_can_edit;
            control.state('add-lock');
        }
    }]
}).addTo(map);

var addPointOnLoad = (lat, long, text, ident_cely,stav) => {
    PROJEKT_IDENT_CELY=ident_cely;
    if (ident_cely) {
        L.marker(amcr_static_coordinate_precision_wgs84([lat, long]), { icon: pinIconYellowDf, zIndexOffset: 2000 })
        .bindTooltip(text)
        .bindPopup(text)
        .addTo(poi_sugest);
    } else {
        L.marker(amcr_static_coordinate_precision_wgs84([lat, long]), { icon: pinIconYellowDf, zIndexOffset: 2000 })
        .addTo(poi_sugest);
    }

    map.setView([lat, long], 12)
}

var addProjektWithoutPointOnLoad = (ident_cely) => {
    PROJEKT_IDENT_CELY=ident_cely;
}

map.on('moveend', function () {
    switchMap(false);
});


heatPoints = heatPoints.map(function (p) {
    var bounds = map.getBounds();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();
    if (northWest.lat >= p[0] && southEast.lat <= p[0]) {
        if (northWest.lng <= p[1] && southEast.lng >= p[1]) {
            return [p[0], p[1]];
        }
    }
});


map.on('click', function (e) {
    const addPointToPoiLayer = (point_leaf, text) => {
        if (global_map_can_edit) {
            poi_correct.clearLayers();
            L.marker(point_leaf, { icon: pinIconRedDf }).bindPopup(text).addTo(poi_correct);
            const getUrl = window.location;
            const select = $("input[name='hlavni_katastr']");
            if (select) {
                fetch(getUrl.protocol + "//" + getUrl.host + `/heslar/mapa-zjisti-katastr/?long=${point_leaf[1]}&lat=${point_leaf[0]}`)
                    .then(response => response.json())
                    .then(response => {
                        if (ORIGIN_KATASTR.length == 0) {
                            ORIGIN_KATASTR = select.val();
                        }
                        select.val(response['value']);
                    })
            }
        }
    }

    let point_leaf = amcr_static_coordinate_precision_wgs84([e.latlng.lat, e.latlng.lng]);
    if (!global_measuring_toolbox._measuring)
        if (point_leaf[1] >= 12.2401111182 && point_leaf[1] <= 18.8531441586 && point_leaf[0] >= 48.5553052842 && point_leaf[0] <= 51.1172677679)
            if (map.getZoom() > 15) {
                try {
                    //console.log("Position is: "+corX+" "+corY)
                    document.getElementById('id_coordinate_x2').value = point_leaf[0]
                    document.getElementById('id_coordinate_x1').value = point_leaf[1]
                } catch (e) {
                    console.log("Error: Element coordinate_x1/x2 doesn exists")
                }
                addPointToPoiLayer(point_leaf, [map_translations['SelectedLocation']]); // 'Vámi vybraná poloha záměru'

            } else {
                var zoom = 2;
                if (map.getZoom() < 10) zoom += 2;
                else if (map.getZoom() < 13) zoom += 1;

                map.setView(e.latlng, map.getZoom() + zoom);
            }
});

map.on('overlayadd', function(eventlayer){
    console.log("pridat mapu")
    if(eventlayer.layer===poi_p1 || eventlayer.layer===poi_p2 || eventlayer.layer===poi_p3 || eventlayer.layer===poi_p46 || eventlayer.layer===poi_p78){
        switchMap(false)
    }
});

map.on('overlayremove', function(eventlayer){
    console.log("ubrat mapu")
    if(eventlayer.layer===poi_p1 || eventlayer.layer===poi_p2 || eventlayer.layer===poi_p3 || eventlayer.layer===poi_p46 || eventlayer.layer===poi_p78){
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
        e.popup._source.closeTooltip()
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

var addPointToPoiLayer = (st_text, layer, text, overview = false, presnost=4) => {
    //addLogText("arch_z_detail_map.addPointToPoiLayer")
    let coor = []
    let myIco = { icon: pinIconGreenPoint };
    let myIco2 = { icon: pinIconGreenHW };
    let myColor = { color: "rgb(151, 0, 156)" };
    let myColorGreen = { color: "rgb(50, 89, 46)" };
    if(presnost==4){
        myIco = { icon: pinIconGreenHW};
    }

    if (st_text.includes("POLYGON") && presnost!=4) {
        st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0].replace("(", "")]))
        })
        L.polygon(coor, myColorGreen)
        .bindTooltip(text+' ('+presnost+')', { sticky: true })
        .bindPopup("").on("click",onMarkerClick.bind(null,text))
        .addTo(layer);
    } else if (st_text.includes("LINESTRING")) {
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]))
        })
        L.polyline(coor, myColorGreen)
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
        //console.log(coor)
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

switchMap = function (overview = false) {
    var bounds = map.getBounds();
    let zoom = map.getZoom();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();
    if (global_map_can_load_projects) {
        if (overview || bounds.northWest != boundsLock.northWest || !boundsLock.northWest) {
            console.log("Change: " + northWest + "  " + southEast + " " + zoom);
            boundsLock = bounds;
            let xhr_proj = new XMLHttpRequest();            
            xhr_proj.open('POST', '/projekt/mapa-projekty');           
            xhr_proj.setRequestHeader('Content-type', 'application/json');
            if (typeof global_csrftoken !== 'undefined') {
                xhr_proj.setRequestHeader('X-CSRFToken', global_csrftoken);
            }
            map.spin(false);
            map.spin(true);
            xhr_proj.send(JSON.stringify(
                {
                    'northWest': northWest,
                    'southEast': southEast,
                    'zoom': zoom,
                    'p1':map.hasLayer(poi_p1),
                    'p2':map.hasLayer(poi_p2),
                    'p3':map.hasLayer(poi_p3),
                    'p46':map.hasLayer(poi_p46),
                    'p78':map.hasLayer(poi_p78),
                }));
            xhr_proj.onload = function () {
                //poi_other.clearLayers();
                poi_p1.clearLayers();
                poi_p2.clearLayers();
                poi_p3.clearLayers();
                poi_p46.clearLayers();
                poi_p78.clearLayers();
                heatPoints = []
                map.removeLayer(heatLayer);
                let resAl = JSON.parse(this.responseText).algorithm
                if (resAl == "detail") {
                    let resPoints = JSON.parse(this.responseText).points
                    resPoints.forEach((i) => {
                        let ge = i.geom.split("(")[1].split(")")[0];
                        let stav=null;
                        switch(i.stav){
                            case 'P1': stav=poi_p1;break;
                            case 'P2': stav=poi_p2;break;
                            case 'P3': stav=poi_p3;break;
                            case 'P4-P6': stav=poi_p46;break;
                            case 'P7-P8': stav=poi_p78;break;
                            default: stav=null
                        }
                        if(i.ident_cely==PROJEKT_IDENT_CELY){
                            stav=poi_sugest;
                        }
                        if(stav!=null){
                           L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconPurpleDf, zIndexOffset: 1000 })
                           .bindTooltip(i.ident_cely+' ('+i.stav+')')
                           .bindPopup('<a href="/projekt/detail/'+i.ident_cely+'" target="_blank">'+i.ident_cely+'</a>')
                           .addTo(stav)
                        }
                    })
                } else {
                    let resHeat = JSON.parse(this.responseText).heat
                    /*resHeat.forEach((i) => {
                        geom = i.geom.split("(")[1].split(")")[0].split(" ");
                        for (let j = 0; j < i.pocet; j++) {
                            heatPoints.push([geom[1], geom[0]])//chyba je to geome
                        }
                    })*/
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
                    //console.log({max:maxHeat,data:heatPoints})
                    heatLayer.setData({max:maxHeat,data:heatPoints})
                    //heatLayer = L.heatLayer(heatPoints, heatmapOptions);
                    map.addLayer(heatLayer);
                    poi_p1.clearLayers();
                    poi_p2.clearLayers();
                    poi_p3.clearLayers();
                    poi_p46.clearLayers();
                    poi_p78.clearLayers();

                }
                map.spin(false);
                //console.log("loaded")
            };
        }
    }
}

window.addEventListener("load", function(){
    let xhr_pian = new XMLHttpRequest();
    xhr_pian.open('POST', '/projekt/mapa-pian');
    if (typeof global_csrftoken !== 'undefined') {       
        xhr_pian.setRequestHeader('X-CSRFToken', global_csrftoken);
    }
    xhr_pian.send(JSON.stringify(
        {
            'northWest': {lat: 51.94436, lng: 6.745605},
            'southEast': {lat: 48.35635, lng: 23.576660},
            'zoom': 6,
            'projekt_ident_cely':PROJEKT_IDENT_CELY
        }));
    xhr_pian.onload = function () {
        try{
            poi_pian.clearLayers(poi_pian);
            let resPoints = JSON.parse(this.responseText).points
            if(resPoints.length==0)control.removeLayer(poi_pian);
            resPoints.forEach((i) => {
                addPointToPoiLayer(i.geom, poi_pian, i.ident_cely, true,i.presnost)
            })
            map.spin(false);
        } catch(e){map.spin(false);}
    };

    let xhr_pas = new XMLHttpRequest();
    xhr_pas.open('POST', '/projekt/mapa-pas');
    if (typeof global_csrftoken !== 'undefined') {        
        xhr_pas.setRequestHeader('X-CSRFToken', global_csrftoken);            
    }
    xhr_pas.send(JSON.stringify(
        {
            'northWest': {lat: 51.94436, lng: 6.745605},
            'southEast': {lat: 48.35635, lng: 23.576660},
            'zoom': 6,
            'projekt_ident_cely':PROJEKT_IDENT_CELY
        }));
    xhr_pas.onload = function () {
        try{
            poi_sn.clearLayers();
            let resPoints = JSON.parse(this.responseText).points
            if(resPoints.length==0)control.removeLayer(poi_sn);
            resPoints.forEach((i) => {
                let ge = i.geom.split("(")[1].split(")")[0];
                L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconGreenPin })
                .bindTooltip(i.ident_cely, { sticky: true })
                .bindPopup('<a href="/pas/detail/'+i.ident_cely+'" target="_blank">'+i.ident_cely+'</a>')
                .addTo(poi_sn)
            })
            map.spin(false);
        } catch(e){map.spin(false);}
        };        
});
