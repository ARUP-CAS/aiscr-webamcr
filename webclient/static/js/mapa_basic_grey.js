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


var cuzkWMS = L.tileLayer.wms('https://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 18, maxNativeZoom: 18, minZoom: 11, opacity: 0.5 }),
    cuzkWMS2 = L.tileLayer.wms('https://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom: 18, maxNativeZoom: 18, minZoom: 7, opacity: 0.5 }),
    cuzkOrt = L.tileLayer.wms('	https://ags.cuzk.cz/arcgis1/services/ORTOFOTO/MapServer/WMSServer?', { layers: '0', maxZoom: 18, maxNativeZoom: 18, minZoom: 1 }),
    cuzkEL = L.tileLayer.wms('https://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 18, maxNativeZoom: 18, minZoom: 1 }),
    cuzkZM = L.tileLayer('https://ags.cuzk.cz/arcgis1/rest/services/ZTM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { maxZoom: 18, maxNativeZoom: 13, minZoom: 0 }),
    npuOchrana = L.tileLayer.wms('https://geoportal.npu.cz/arcgis/services/Experimental/TM_proAMCR/MapServer/WMSServer?', { layers: '2,3,4,5,7,8,10,11', maxZoom: 18, maxNativeZoom: 15, minZoom: 6, format:'image/png', transparent:true });

    var poi = L.layerGroup();

var JTSKcrs = L.extend({}, L.CRS, {
    projection: {
        project: function(latlng) {
            var coords = convertToJTSK(latlng.lng, latlng.lat, height=0)
            return L.point(coords[0], coords[1]);
        },
        unproject: function(point) {
        
            var latlng= convertToWGS84(point.x, point.y)
            return L.latLng(latlng[1], latlng[0]); 
        },
        bounds: L.bounds([ -931374.5041534386, -1265741.5915737757], [-403476.6008465581, -896504.1794262241])
    },

    distance: function (latlng1, latlng2) {
        var coords1 = convertToJTSK(latlng1.lng, latlng1.lat, height=0)
        var coords2 = convertToJTSK(latlng2.lng, latlng2.lat, height=0)
        return Math.sqrt(Math.pow(coords2[0]-coords1[0],2)+Math.pow(coords2[1]-coords1[1],2))
    },
    code: 'EPSG:5514',
    transformation: new L.Transformation(1, 925000, -1, -920000), 
    scale: function(zoom) {
        return 1/(2048.260096520193* Math.pow(2,-zoom));
    },
    zoom: function (scale) {
        return Math.log(2048.26009652019 * scale) / Math.log(2);
    },   
    infinite: false,
});

var map = L.map('projectMap',{crs: JTSKcrs, attributionControl:false,zoomControl:false,  layers: [cuzkZM,poi]}).setView([49.84, 15.17], 1);


var baseLayers = {
    [map_translations['cuzkzakladniMapyCr']]: cuzkZM,
    [map_translations['cuzkOrtofotomapa']]: cuzkOrt,
    [map_translations['cuzkStinovanyeelief5G']]: cuzkEL,
};

var overlays = {
    [map_translations['cuzkKatastralniMapa']]: cuzkWMS,
    [map_translations['cuzkKatastralniUzemi']]: cuzkWMS2,
    [map_translations['npuPamatkovaOchrana']]: npuOchrana,
    [map_translations['lokalizace']]: poi
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
    layerKN:cuzkWMS
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

//Get Current Location
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    } else {
        x.innerHTML = [map_translations['CurrentLocationError']]; // "Geolocation is not supported by this browser."
    }
}
