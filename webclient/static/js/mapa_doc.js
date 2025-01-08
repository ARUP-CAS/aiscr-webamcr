var global_map_can_edit = true;
var point_global_WGS84 = [0, 0];
var point_global_JTSK = [0, 0];

var poi_model= L.layerGroup();
var poi_all = L.markerClusterGroup({ disableClusteringAtZoom: 20 })

var map = L.map('projectMap',{attributionControl:false,zoomControl:false, layers: [cuzkZM,poi_model]}).setView(init_position, init_zoom_mercator);

var baseLayers = {
    [map_translations['cuzkzakladniMapyCr']]: cuzkZM,
    [map_translations['cuzkOrtofotomapa']]: cuzkOrt,
    [map_translations['cuzkStinovanyeelief5G']]: cuzkEL,
    [map_translations['openStreetMapSeda']]: osmGrey,
};

var overlays = {
   [map_translations['cuzkKatastralniMapa']]: cuzkWMS,
   [map_translations['cuzkKatastralniUzemi']]: cuzkWMS2,
   [map_translations['npuPamatkovaOchrana']]: npuOchrana,
   [map_translations['Location3D']]:poi_model,
   [map_translations['Library3D']]:poi_all,
};

var global_map_layers = L.control.layers(baseLayers,overlays).addTo(map);
L.control.scale({imperial: false, metric: true,  maxWidth: 100}).addTo(map);

var searchControl=new L.Control.Search({
    position:'topleft',
    initial: false,
    marker: false,
    propertyName: 'text',
    propertyMagicKey:'magicKey',
    minLength:3,
    translations:leaflet_search_translations,
    layerKN:cuzkWMS, 
    zoom:6
}).addTo(map);

map.addControl(new L.Control.Fullscreen({
    title: {
        'false': [map_translations['FullscreenTitle']],
        'true': [map_translations['FullscreenTitleClose']]
    }
}));
map.addControl(new L.control.zoom(
    {
        zoomInText: '+',
        zoomInTitle: [map_translations['zoomInTitle']],
        zoomOutText: '-',
        zoomOutTitle: [map_translations['zoomOutTitle']]
    }))

let global_measuring_toolbox=new L.control.measure(
    {
        title: [map_translations['MeasureTitle']],
        icon:'<img src="'+static_url+'img/ruler-bold-32.png" style="width:20px"/>'
    });
map.addControl(global_measuring_toolbox);

map.addControl(new L.control.coordinates(
    {
    position:"bottomright",
    useDMS:false,
    decimals: 7,
	decimalSeperator: ",",
    labelTemplateLat:"N {y}",
    labelTemplateLng:"E {x}",
    useLatLngOrder:false,
    centerUserCoordinates: true,
    markerType: null
    }).addTo(map));

map.on('click', function (e) {
    if (!global_measuring_toolbox._measuring) {        
        if (global_map_can_edit) {
                let point_leaf= amcr_static_coordinate_precision_wgs84([e.latlng.lat, e.latlng.lng]);
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
});

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
        map.setView(point_leaf, zoom_mercator);
    }
    point_global_WGS84 = [...point_leaf].reverse()
}

var addReadOnlyUniquePointToPoiLayer = (point_leaf, ident_cely) => {
    addUniquePointToPoiLayer(point_leaf, ident_cely, true)
};

var replace_coor = () => {
    var x1='id_visible_x1';
    var x2='id_visible_x2';
    document.getElementById(x1).value=(document.getElementById(x1).value.replace(".",","));
    document.getElementById(x2).value=(document.getElementById(x2).value.replace(".",","));
}

// Načtení stavu při načtení stránky
loadMapState('doc');
// Připojení eventů pro sledování změn
addEventLayerChange('doc');

map.on('moveend', function () {
    switchMap();
});

$(document).ready(function () {
    switchMap();
})

//načtení 3d dokumentů při každém překreslení mapy
switchMap = function () {
    var bounds = map.getBounds();
    let zoom = map.getZoom();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();

    let xhr_3d_all = new XMLHttpRequest();
    xhr_3d_all.open('POST', '/dokument/model/mapa-3d');
    xhr_3d_all.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr_3d_all.setRequestHeader('X-CSRFToken', global_csrftoken);
    }
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

