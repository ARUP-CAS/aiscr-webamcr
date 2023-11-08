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
var heatLayer = L.heatLayer(heatPoints, heatmapOptions);

var global_clusters = false;
var global_heat = false;

var overlays = {
    [map_translations['cuzkKatastralniMapa']]: cuzkWMS,
    "ČÚZK - Katastrální území": cuzkWMS2,
    "Lokalizace projektu":poi_sugest,
    "Projekty - zapsané":poi_p1,
    "Projekty - přihlášené":poi_p2,
    "Projekty - běžící":poi_p3,
    "Projekty - realizované":poi_p46,
    "Projekty - zrušené":poi_p78,
    "Samostatné nálezy projektu":poi_sn,
    "PIAN projektu":poi_pian,
};

global_map_layers.remove(map);//remove previous overlay
L.control.layers(baseLayers, overlays).addTo(map);

L.easyButton('bi bi-skip-backward-fill', function () {
    poi_correct.clearLayers();
    if (poi_sugest.getLayers().length) {
        let ll = poi_sugest.getLayers()[0]._latlng;
        map.setView(ll, 18);
        try {
            document.getElementById('id_latitude').value = ll.lat;
            document.getElementById('id_longitude').value = ll.lng;
        } catch (e) {
            console.log("Error: Element id_latitude/latitude doesn exists")
        }
        //Vratit puvodni katastr
        const select = $("input[name='hlavni_katastr']");
        if (global_map_can_edit && select && ORIGIN_KATASTR.length > 1) {
            select.val(ORIGIN_KATASTR);

        }
    }
}, 'Výchozí stav ').addTo(map)


var button_map_lock = L.easyButton({
    states: [{
        stateName: 'add-lock',
        icon: 'bi bi-lock',
        title: 'Vypnout‌ ‌editaci‌‌',
        onClick: function (control) {
            global_map_can_edit = !global_map_can_edit;
            control.state('remove-lock');
        }
    }, {
        icon: 'bi bi-geo-alt',
        stateName: 'remove-lock',
        title: 'Zapnout‌ ‌editaci‌',
        onClick: function (control) {
            global_map_can_edit = !global_map_can_edit;
            control.state('add-lock');
        }
    }]
}).addTo(map);

var addPointOnLoad = (lat, long, text, ident_cely) => {
    PROJEKT_IDENT_CELY=ident_cely;
    if (text) {
        L.marker(amcr_static_coordinate_precision_wgs84([lat, long]), { icon: pinIconYellowDf, zIndexOffset: 2000 }).bindPopup(text).addTo(poi_sugest);
    } else {
        L.marker(amcr_static_coordinate_precision_wgs84([lat, long]), { icon: pinIconYellowDf, zIndexOffset: 2000 }).addTo(poi_sugest);
    }

    map.setView([lat, long], 18)
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
    const addPointToPoiLayer = (lat, long, text) => {
        if (global_map_can_edit) {
            poi_correct.clearLayers();
            L.marker([lat, long], { icon: pinIconRedDf }).bindPopup(text).addTo(poi_correct);
            const getUrl = window.location;
            const select = $("input[name='hlavni_katastr']");
            if (select) {
                fetch(getUrl.protocol + "//" + getUrl.host + `/heslar/mapa-zjisti-katastr/?long=${long}&lat=${lat}`)
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

    let [corX, corY] = amcr_static_coordinate_precision_wgs84([e.latlng.lat, e.latlng.lng]);
    if (!global_measuring_toolbox._measuring)
        if (corY >= 12.2401111182 && corY <= 18.8531441586 && corX >= 48.5553052842 && corX <= 51.1172677679)
            if (map.getZoom() > 15) {
                try {
                    //console.log("Position is: "+corX+" "+corY)
                    document.getElementById('id_latitude').value = corX
                    document.getElementById('id_longitude').value = corY
                } catch (e) {
                    console.log("Error: Element id_latitude/latitude doesn exists")
                }
                addPointToPoiLayer(corX, corY, 'Vámi vybraná poloha záměru');

            } else {
                var zoom = 2;
                if (map.getZoom() < 10) zoom += 2;
                else if (map.getZoom() < 13) zoom += 1;

                map.setView(e.latlng, map.getZoom() + zoom);
            }
});

var addPointToPoiLayer = (st_text, layer, text, overview = false, presnost4=false) => {
    //addLogText("arch_z_detail_map.addPointToPoiLayer")
    let coor = []
    let myIco = { icon: pinIconGreenPoint };
    let myIco2 = { icon: pinIconGreenleHW };
    let myColor = { color: "rgb(151, 0, 156)" };
    if(presnost4){
        myIco = { icon: pinIconGreenHW};
    }

    if (st_text.includes("POLYGON") && !presnost4) {
        st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0].replace("(", "")]))
        })
        L.polygon(coor, myColor).bindTooltip(text, { sticky: true }).addTo(layer);
    } else if (st_text.includes("LINESTRING")) {
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]))
        })
        L.polyline(coor, myColor).bindTooltip(text, { sticky: true }).addTo(layer);
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
            L.marker(amcr_static_coordinate_precision_wgs84([x0 / c0, x1 / c0]), myIco2).bindTooltip(text).addTo(layer);
        } else {
            L.marker(amcr_static_coordinate_precision_wgs84([x0 / c0, x1 / c0]), myIco).bindTooltip(text).addTo(layer);
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
            let xhr_pas = new XMLHttpRequest();
            let xhr_pian = new XMLHttpRequest();
            xhr_proj.open('POST', '/projekt/akce-get-projekty');
            xhr_pas.open('POST', '/projekt/akce-get-projekt-pas');
            xhr_pian.open('POST', '/projekt/akce-get-projekt-pian');
            xhr_proj.setRequestHeader('Content-type', 'application/json');
            if (typeof global_csrftoken !== 'undefined') {
                xhr_proj.setRequestHeader('X-CSRFToken', global_csrftoken);
                xhr_pas.setRequestHeader('X-CSRFToken', global_csrftoken);
                xhr_pian.setRequestHeader('X-CSRFToken', global_csrftoken);
            }
            map.spin(false);
            map.spin(true);
            xhr_proj.send(JSON.stringify(
                {
                    'northWest': northWest,
                    'southEast': southEast,
                    'zoom': zoom,
                }));
            xhr_pas.send(JSON.stringify(
                    {
                        'northWest': northWest,
                        'southEast': southEast,
                        'zoom': zoom,
                        'projekt_ident_cely':PROJEKT_IDENT_CELY
                    }));
            xhr_pian.send(JSON.stringify(
                {
                    'northWest': northWest,
                    'southEast': southEast,
                    'zoom': zoom,
                    'projekt_ident_cely':PROJEKT_IDENT_CELY
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
                            L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconPurpleDf, zIndexOffset: 1000 }).bindPopup(i.ident_cely).addTo(stav)
                        }
                    })
                } else {
                    let resHeat = JSON.parse(this.responseText).heat
                    resHeat.forEach((i) => {
                        geom = i.geom.split("(")[1].split(")")[0].split(" ");
                        for (let j = 0; j < i.pocet; j++) {
                            heatPoints.push([geom[1], geom[0]])//chyba je to geome
                        }
                    })
                    heatLayer = L.heatLayer(heatPoints, heatmapOptions);
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
            xhr_pas.onload = function () {
                try{
                    poi_sn.clearLayers();
                    let resPoints = JSON.parse(this.responseText).points
                    resPoints.forEach((i) => {
                        let ge = i.geom.split("(")[1].split(")")[0];
                        L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconGreenPin }).bindPopup(i.ident_cely).addTo(poi_sn)
                    })

                    map.spin(false);
                } catch(e){map.spin(false);}
            };
            xhr_pian.onload = function () {
                try{
                    poi_pian.clearLayers(poi_pian);
                    let resPoints = JSON.parse(this.responseText).points
                    resPoints.forEach((i) => {
                        addPointToPoiLayer(i.geom, poi_pian, i.ident_cely, true,i.presnost==4)
                    })
                    map.spin(false);
                } catch(e){map.spin(false);}
            };
        }
    }
}
