/*
 * mapa_basic_functions_mercator.js — vytvoření mapy pro mapový filtr knihovny 3D.
 *
 * Obdoba mapa_basic_functions.js, ale ve výchozím CRS (Web Mercator / EPSG:3857) s dlaždicemi
 * z mapa_settings_mercator.js. Knihovna 3D je na rozdíl od ostatních modulů v Mercatoru, ne v S-JTSK.
 * Vytvoří globální `map` nad divem #projectMap a přidá základní ovládací prvky; další logiku
 * (kreslení výběru, datová vrstva) doplňuje mapa_filter.js.
 */
var poi = L.layerGroup();

var map = L.map("projectMap", {
    attributionControl: true,
    zoomControl: false,
    layers: [osmGrey, poi],
}).setView(init_position, init_zoom_mercator);

var baseLayers = {
    [map_translations["cuzkzakladniMapyCr"]]: cuzkZM,
    [map_translations["cuzkOrtofotomapa"]]: cuzkOrt,
    [map_translations["cuzkStinovanyeelief5G"]]: cuzkEL,
    [map_translations["openStreetMapSeda"]]: osmGrey,
};

var overlays = {
    [map_translations["cuzkKatastralniMapa"]]: cuzkWMS,
    [map_translations["cuzkKatastralniUzemi"]]: cuzkWMS2,
    [map_translations["npuPamatkovaOchrana"]]: npuOchrana,
};

var global_map_layers = L.control.layers(baseLayers, overlays).addTo(map);
L.control.scale({ imperial: false, metric: true, maxWidth: 100 }).addTo(map);

var searchControl = new L.Control.Search({
    position: "topleft",
    initial: false,
    marker: false,
    propertyName: "text",
    propertyMagicKey: "magicKey",
    minLength: 2,
    translations: leaflet_search_translations,
    layerKN: cuzkWMS,
    zoom: 6,
}).addTo(map);

map.addControl(
    new L.Control.Fullscreen({
        title: {
            false: [map_translations["FullscreenTitle"]],
            true: [map_translations["FullscreenTitleClose"]],
        },
    })
);
map.addControl(
    new L.control.zoom({
        zoomInText: "+",
        zoomInTitle: [map_translations["zoomInTitle"]],
        zoomOutText: "-",
        zoomOutTitle: [map_translations["zoomOutTitle"]],
    })
);

let global_measuring_toolbox = new L.control.measure({
    title: [map_translations["MeasureTitle"]],
    icon: '<img src="' + static_url + 'img/ruler-bold-32.png" style="width:20px"/>',
});
map.addControl(global_measuring_toolbox);

map.addControl(
    new L.control.coordinates({
        position: "bottomright",
        useDMS: false,
        decimals: 7,
        decimalSeperator: ",",
        labelTemplateLat: "N {y}",
        labelTemplateLng: "E {x}",
        useLatLngOrder: false,
        centerUserCoordinates: true,
        markerType: null,
    }).addTo(map)
);
