var global_map_can_edit = true;

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

    var poi = L.layerGroup();
    var point_global_WGS84 = [0, 0];
    var point_global_JTSK = [0, 0];
    var lock = false;

    //var mbAttr = 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
    //		'<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
    //		'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    //	mbUrl = 'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw';

    //var grayscale   = L.tileLayer(mbUrl, {id: 'mapbox.light', attribution: mbAttr}),
    //    streets  = L.tileLayer(mbUrl, {id: 'mapbox.streets',   attribution: mbAttr});
    var osmColor = L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM map', maxZoom: 19.99, minZoom: 6 }),
        osmGrey = L.tileLayer.grayscale('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM grey map', maxZoom: 19.99, minZoom: 6 }),
        cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 20.99, minZoom: 17 }),
        cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/ortofoto_wm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom: 19.99, minZoom: 6 }),
        cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 20, minZoom: 6 }),
        cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/zmwm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 19.99, minZoom: 6 });

    var map = L.map('projectMap', {
        center: [49.84, 15.17],
        zoom: 7,
        layers: [cuzkZM, poi],
        fullscreenControl: true,
    }).setView([49.84, 15.17], 7);;

    var baseLayers = {
        "Mapa ČR": osmColor,
        "Mapa ČR šedá": osmGrey,
        "Katastrální mapa": cuzkWMS,
        "Základní mapa": cuzkZM,
        "Ortofotomapa": cuzkOrt,
        "Stínovaný reliéf 5G": cuzkEL,
    };

    var overlays = {
        "AMČR Zájmové body": poi
    };

    map.on('click', function (e) {
        corX = e.latlng.lat;
        corY = e.latlng.lng;

//        if(('{{context.archivovano}}' === 'undefined' || '{{context.archivovano}}'=='False')){
          if(global_map_can_edit){
            if (!lock) {
                if (map.getZoom() > 15) {
                    //jtsk_coor = converToJTSK(corX, corY);
                    point_global_WGS84 = [Math.round(corX * 1000000) / 1000000, Math.round(corY * 1000000) / 1000000]
                    //point_global_JTSK = [-Math.round(jtsk_coor[0] * 100) / 100, -Math.round(jtsk_coor[1] * 100) / 100]

                    //if (document.getElementById('detector_system_coordinates').value == 1) {
                        document.getElementById('id_coordinate_x').value = point_global_WGS84[0]
                        document.getElementById('id_coordinate_y').value = point_global_WGS84[1]
                        document.getElementById('id_vyska').value = point_global_WGS84[0]
                        document.getElementById('id_sirka').value = point_global_WGS84[1]
                    /*} else if (document.getElementById('detector_system_coordinates').value == 2) {
                        document.getElementById('id_coordinate_x').value = point_global_JTSK[0]
                        document.getElementById('id_coordinate_y').value = point_global_JTSK[1]
                    }*/
                    $("#vyska").change();
                    $("#sirka").change();
                    addUniquePointToPoiLayer(corX, corY, '', false)
                } else {
                        map.setView(e.latlng, map.getZoom() + 2)
                }
            }
            }
    });

    var is_in_czech_republic = (corX,corY) => {
        console.log("Test coordinates for bounding box");

        //if(document.getElementById('detector_system_coordinates').value ==1){
            if(corY>=12.2401111182 && corY<=18.8531441586 && corX>=48.5553052842 && corX<=51.1172677679){

                return true;
            }else {
                console.log("Coordinates not inside CR");
                point_global_WGS84 = [0, 0];
                poi.clearLayers();
                return false
            }
        /*} else {
            if(corX>=-889110.16  && corX<=-448599.79 && corY>=-1231915.96 && corY<=-892235.44){
                return true
            } else {
                console.log("Coordinates not inside CR");
            point_global_WGS84 = [0, 0];
            poi.clearLayers();
            return false;
        }
    }*/
    }

    /*let set_numeric_coordinates = async () => {
        corX = document.getElementById('id_coordinate_x').value;
        corY = document.getElementById('id_coordinate_y').value;
        if(is_in_czech_republic(corX,corY)){
            if(document.getElementById('detector_system_coordinates').value ==1){
                jtsk_coor = converToJTSK(corX, corY);
                point_global_WGS84 = [Math.round(corX * 1000000) / 1000000, Math.round(corY * 1000000) / 1000000]
                point_global_JTSK = [-Math.round(jtsk_coor[0] * 100) / 100, -Math.round(jtsk_coor[1] * 100) / 100]
                return true;
            } else if(document.getElementById('detector_system_coordinates').value ==2){
                $.getJSON( "https://epsg.io/trans?x="+Math.round(corX * 100) / 100+"&y="+Math.round(corY * 100) / 100+"&s_srs=5514&t_srs=4326", function(data){
                            point_global_WGS84 = [Math.round(data.y * 1000000) / 1000000, Math.round(data.x * 1000000) / 1000000]
                            point_global_JTSK = [Math.round(corX * 100) / 100, Math.round(corY * 100) / 100]
                            return true;

                        });


            }
        }
        return false;
    }

    var switch_coordinate_system = () => {
        new_system = document.getElementById('detector_system_coordinates').value
        switch_coor_system(new_system)
    }

    var switch_coor_system = (new_system) => {
        console.log("switch system: " + new_system)
        if (new_system == 1 && point_global_WGS84[0] != 0) {
            document.getElementById('id_coordinate_x').value = point_global_WGS84[0]
            document.getElementById('id_coordinate_y').value = point_global_WGS84[1]
            document.getElementById('id_coordinate_x').readOnly = false;
            document.getElementById('id_coordinate_y').readOnly = false;
        } else if (new_system == 2 && point_global_JTSK[0] != 0) {
            document.getElementById('id_coordinate_x').value = point_global_JTSK[0]
            document.getElementById('id_coordinate_y').value = point_global_JTSK[1]
            document.getElementById('id_coordinate_x').readOnly = false;
            document.getElementById('id_coordinate_y').readOnly = false;
        }
    }*/

    var addPointToPoiLayer = (lat, long, text) => {
        L.marker([lat, long]).bindPopup(text).addTo(poi);
    }
    var addUniquePointToPoiLayer = (lat, long, text, zoom = true) => {
        poi.clearLayers()
        L.marker([lat, long]).bindPopup("Vámi vyznačená poloha").addTo(poi);
        if (long && lat && zoom) {
            map.setView([lat, long], 15);
        }

        //if (point_global_WGS84[0] == 0) {
        //    jtsk_coor = converToJTSK(lat, long);
            point_global_WGS84 = [Math.round(lat * 1000000) / 1000000, Math.round(long * 1000000) / 1000000]
        //    point_global_JTSK = [-Math.round(jtsk_coor[0] * 100) / 100, -Math.round(jtsk_coor[1] * 100) / 100]
        //}
    }

    var addReadOnlyUniquePointToPoiLayer = (lat, long, text) => {
        addUniquePointToPoiLayer(lat, long, text, true)
        lock = false;
    }

    L.control.layers(baseLayers, overlays).addTo(map);
    L.control.scale(metric = "true").addTo(map);

    //addPointToPoiLayer(49.96885475762718,16.090292930603033,'Ukázka POI1')
    //addPointToPoiLayer(49.880477638742555,15.347900390625002,'Ukázka POI2')

    //Get Current Location
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(showPosition);
        } else {
            x.innerHTML = "Geolocation is not supported by this browser.";
        }
    }
    //Get position - needed in GetLocation method
    function showPosition(position) {
        var latitude = position.coords.latitude;
        var longitude = position.coords.longitude;
        var latlng = new L.LatLng(latitude, longitude);

        map.setView(latlng, 16);
        addUniquePointToPoiLayer(latitude, longitude, '', false)

        //document.getElementById('detector_system_coordinates').value = 1
        point_global_WGS84 = [Math.round(latitude * 1000000) / 1000000, Math.round(longitude * 1000000) / 1000000]
        document.getElementById('id_coordinate_x').value = point_global_WGS84[0]
        document.getElementById('id_coordinate_y').value = point_global_WGS84[1]
        document.getElementById('id_vyska').value = point_global_WGS84[0]
        document.getElementById('id_sirka').value = point_global_WGS84[1]

        L.marker(latlng).addTo(poi)
            .bindPopup("Vaše současná poloha")
            .openPopup();
    };
