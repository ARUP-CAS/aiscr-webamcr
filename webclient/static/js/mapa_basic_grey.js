// https://github.com/Zverik/leaflet-grayscale
    /*
     * L.TileLayer.Grayscale is a regular tilelayer with grayscale makeover.
     */

L.TileLayer.Grayscale = L.TileLayer.extend({
    options: {
        quotaRed: 21,
        quotaGreen: 71,
        quotaBlue: 8,
        quotaDividerTune: 0,
        quotaDivider: function () {
            return this.quotaRed + this.quotaGreen + this.quotaBlue + this.quotaDividerTune;
        }
    },

    initialize: function (url, options) {
        options = options || {}
        options.crossOrigin = true;
        L.TileLayer.prototype.initialize.call(this, url, options);

        this.on('tileload', function (e) {
            this._makeGrayscale(e.tile);
        });
    },

    _createTile: function () {
        var tile = L.TileLayer.prototype._createTile.call(this);
        tile.crossOrigin = "Anonymous";
        return tile;
    },

    _makeGrayscale: function (img) {
        if (img.getAttribute('data-grayscaled'))
            return;

        img.crossOrigin = '';
        var canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        var ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);

        var imgd = ctx.getImageData(0, 0, canvas.width, canvas.height);
        var pix = imgd.data;
        for (var i = 0, n = pix.length; i < n; i += 4) {
            pix[i] = pix[i + 1] = pix[i + 2] = (this.options.quotaRed * pix[i] + this.options.quotaGreen * pix[i + 1] + this.options.quotaBlue * pix[i + 2]) / this.options.quotaDivider();
        }
        ctx.putImageData(imgd, 0, 0);
        img.setAttribute('data-grayscaled', true);
        img.src = canvas.toDataURL();
    }
});

L.tileLayer.grayscale = function (url, options) {
    return new L.TileLayer.Grayscale(url, options);
};


var     osmGrey = L.tileLayer.grayscale('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM grey map', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
        cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom:25, maxNativeZoom: 20, minZoom: 17, opacity: 0.5 }),
        cuzkWMS2 = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom:25, maxNativeZoom: 20, minZoom: 12, opacity: 0.5 }),
        cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis1/rest/services/ORTOFOTO_WM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
        cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 25, maxNativeZoom: 20, minZoom: 6 }),
        cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis1/rest/services/ZTM_WM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 25,maxNativeZoom:19, minZoom: 6 }),
        npuOchrana = L.tileLayer.wms('https://geoportal.npu.cz/arcgis/services/Experimental/TM_proAMCR/MapServer/WMSServer?', { layers: '2,3,4,5,7,8,10,11', maxZoom: 25, maxNativeZoom: 20, minZoom: 12, format:'image/png', transparent:true });
var poi = L.layerGroup();
var map = L.map('projectMap',{attributionControl:false,zoomControl:false,  layers: [cuzkZM,poi]}).setView([49.84, 15.17], 7);


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
    [map_translations['lokalizace']]: poi
};

var global_map_layers = L.control.layers(baseLayers,overlays).addTo(map);
L.control.scale(metric = "true").addTo(map);
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

var searchControl=new L.Control.Search({
    position:'topleft',
    sourceData: searchByAjax,
    initial: false,
    zoom: 12,
    marker: false,
    textPlaceholder: [map_translations['SearchText']],
    textCancel: [map_translations['SearchTextCancel']],
    propertyName: 'text',
    propertyMagicKey:'magicKey',
    propertyMagicKeyUrl:'https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Vyhledavaci_sluzba_nad_daty_RUIAN/MapServer/exts/GeocodeSOE/tables/{*}/findAddressCandidates?outSR={"wkid":4258}&f=json',
    textErr: [map_translations['SearchTextError']],
    minLength:3
}).addTo(map);

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
    useLatLngOrder:true,
    centerUserCoordinates: true,
    markerType: null
    }).addTo(map));

//Get Current Location
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    } else {
        x.innerHTML = [map_translations['CurrentLocationError']]; // "Geolocation is not supported by this browser."
    }
}

function compareSearchResult( a, b ) {
    if ( a.text < b.text ){
      return -1;
    }
    if ( a.text > b.text ){
      return 1;
    }
    return 0;
}

function searchByAjax(text, callResponse){
	let items1=[];
	let items2=[];

	let ajaxCall=[
    $.ajax({//GeoNames
            url: 'https://ags.cuzk.cz/arcgis/rest/services/GEONAMES/Vyhledavaci_sluzba_nad_daty_GEONAMES/MapServer/exts/GeocodeSOE/suggest?maxSuggestions=100&outSR={"latestWkid":5514,"wkid":102067}&f=json',
            type: 'GET',
            data: { text: text },
            dataType: 'json',
            success: function (json) { items1 = json.suggestions.sort( compareSearchResult );/*addLogText("Vyhledany GeoNames");*/ }
        }),
	$.ajax({//okres
		url:
		'https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Vyhledavaci_sluzba_nad_daty_RUIAN/MapServer/exts/GeocodeSOE/tables/15/suggest?maxSuggestions=10&outSR={"latestWkid":5514,"wkid":102067}&f=json',
		type: 'GET',
		data: {text: text},
		dataType: 'json',
        success: function (json) { items2 = json.suggestions.sort( compareSearchResult );/*addLogText("Vyhledany Okresy");*/ }
		}),

	];
	Promise.all(ajaxCall).then(() => {/*console.log("Vyhledani ukonceno");*/callResponse( [...items2, ...items1]);})
}
