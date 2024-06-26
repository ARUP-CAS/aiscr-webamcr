var global_map_can_edit = false; //editační režim
var global_blocked_by_query_geom= false; //nahraná geometrie ze sessions pro opravu nebo z importu

var global_map_can_grab_geom_from_map = false;
var global_map_element = "id_geom";
var global_map_element_sjtsk = "id_geom_sjtsk";
var global_map_can_load_pians = true;
var global_map_katastry_all = null;
var global_unwanted_popup=null;
var DJ_pians_ident_cely=[];

addLogText("zmena def.geom :" + global_map_element)

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


var osmGrey = L.tileLayer.grayscale('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM grey map', maxZoom: 25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 25, maxNativeZoom: 20, minZoom: 17, opacity: 0.5 }),
    cuzkWMS2 = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom: 25, maxNativeZoom: 20, minZoom: 12, opacity: 0.5 }),
    cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis1/rest/services/ORTOFOTO_WM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom: 25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 25, maxNativeZoom: 20, minZoom: 6 }),
    cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis1/rest/services/ZTM_WM/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 25, maxNativeZoom: 19, minZoom: 6 }),
    npuOchrana = L.tileLayer.wms('https://geoportal.npu.cz/arcgis/services/Experimental/TM_proAMCR/MapServer/WMSServer?', { layers: '2,3,4,5,7,8,10,11', maxZoom: 25, maxNativeZoom: 20, minZoom: 12, format:'image/png', transparent:true });
var global_clusters = false;
var global_heat = false;

var map = L.map('djMap', {
    attributionControl: false,
    layers: [cuzkZM],
    zoomControl: false,
    contextmenu: true,
    contextmenuWidth: 140,
    contextmenuItems: []

}).setView([49.84, 15.17], 8);

var parentGroup = L.markerClusterGroup({ disableClusteringAtZoom: 20 }).addTo(map);
var poi_all =  L.featureGroup.subGroup(parentGroup)
var poi_sn =  L.featureGroup.subGroup(parentGroup)

var poi_sugest = L.layerGroup();
var gm_correct = L.layerGroup();

var poi_dj = L.featureGroup()
var poi_pian_dp = L.featureGroup.subGroup(poi_all)
var poi_pian =  L.featureGroup.subGroup(poi_all)


var poi_model = L.layerGroup();
var heatPoints = [];
var heatmapOptions = settings_heatmap_options;
var heatLayer = new HeatmapOverlay( heatmapOptions);

var drawnItems = new L.FeatureGroup();
var drawnItemsBuffer = new L.FeatureGroup();
map.addLayer(drawnItems);

map.addLayer(poi_sugest);
map.addLayer(poi_pian);
map.addLayer(poi_pian_dp);
map.addLayer(poi_dj);
map.addLayer(poi_all)

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
    [map_translations['lokalizaceProjektu']]: poi_model,
    [map_translations['pianZazamu']]: poi_dj ,
    [map_translations['samostatneNalezy']]: poi_sn,
    [map_translations['pian']]: poi_all,
};

var control = L.control.layers(baseLayers, overlays).addTo(map);
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
    }));

var searchControl = new L.Control.Search({
    position: 'topleft',
    sourceData: searchByAjax,
    initial: false,
    zoom: 12,
    marker: false,
    textPlaceholder: [map_translations['SearchText']],
    textCancel: [map_translations['SearchTextCancel']],
    propertyName: 'text',
    propertyMagicKey: 'magicKey',
    propertyMagicKeyUrl: 'https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Vyhledavaci_sluzba_nad_daty_RUIAN/MapServer/exts/GeocodeSOE/tables/{*}/findAddressCandidates?outSR={"wkid":4258}&f=json',
    textErr: [map_translations['SearchTextError']],
    minLength: 3
}).addTo(map);

var buttons = [
    L.easyButton('bi bi-skip-backward-fill', function () {
        map.setView(poi_sugest.getLayers()[0]._latlng, 18);
        edit_buttons.disable();
    }, [map_translations['DefaultTitle']])]

var edit_buttons = L.easyBar(buttons)
map.addControl(edit_buttons)


L.EditToolbar.Delete.include({
    removeAllLayers: false
});
L.DrawToolbar.include({
    getModeHandlers: function (map) {
        return [
            {
                enabled: this.options.marker,
                handler: new L.Draw.Marker(map, this.options.marker),
                title: L.drawLocal.draw.toolbar.buttons.marker
            },
            {
                enabled: this.options.circlemarker,
                handler: new L.Draw.CircleMarker(map, this.options.circlemarker),
                title: L.drawLocal.draw.toolbar.buttons.circlemarker
            },
            {
                enabled: this.options.polyline,
                handler: new L.Draw.Polyline(map, this.options.polyline),
                title: L.drawLocal.draw.toolbar.buttons.polyline
            },
            {
                enabled: this.options.polygon,
                handler: new L.Draw.Polygon(map, this.options.polygon),
                title: L.drawLocal.draw.toolbar.buttons.polygon
            },
            {
                enabled: this.options.rectangle,
                handler: new L.Draw.Rectangle(map, this.options.rectangle),
                title: L.drawLocal.draw.toolbar.buttons.rectangle
            },
            {
                enabled: this.options.circle,
                handler: new L.Draw.Circle(map, this.options.circle),
                title: L.drawLocal.draw.toolbar.buttons.circle
            }

        ];
    }
});
L.drawLocal = {
    draw: {
        toolbar: {
            actions: {
                title: [map_translations['EditCancelTitle']],
                text: [map_translations['EditCancelText']]
            },
            finish: {
                title: [map_translations['EditFinishTitle']],
                text: [map_translations['EditFinishText']]
            },
            undo: {
                title: [map_translations['EditBackTitle']],
                text: [map_translations['EditBackText']]
            },
            buttons: {
                polyline: [map_translations['EditAddPolyline']],
                polygon: [map_translations['EditAddPolygon']],
                rectangle: [map_translations['EditAddRectangle']],
                circle: [map_translations['EditAddCircle']],
                marker: [map_translations['EditAddMarker']],
                circlemarker: [map_translations['EditAddCirclemarker']]
            }
        },
        handlers: {
            circle: {
                tooltip: {
                    start: [map_translations['EditCircleTooltip']] // 'Pro nakreslení kruhu klikni a táhni.'
                },
                radius: [map_translations['EditRadius']] // 'Poloměr'
            },
            circlemarker: {
                tooltip: {
                    start: [map_translations['EditCirclemarkerTooltip']] // 'Klikni na mapu a umísti kruhovou značku.'
                }
            },
            marker: {
                tooltip: {
                    start: [map_translations['EditMarkerTooltip']] // 'Klikni na mapu a umísti značku.'
                }
            },
            polygon: {
                tooltip: {
                    start: [map_translations['EditPolygonStart']], // 'Pro nakreslení tvaru klikni.'
                    cont: [map_translations['EditPolygonTooltipCont']], // 'Pro pokračování v kresbě klikni.'
                    end: [map_translations['EditPolygonTooltipEnd']] // 'Klikni na první bod k uzavření tvaru.'
                }
            },
            polyline: {
                error: [map_translations['EditPolylineError']], // '<strong>Chyba:</strong> hrany tvaru se nesmějí překrývat!'
                tooltip: {
                    start: [map_translations['EditPolylineStart']], // 'Klikni pro začátek linie.'
                    cont: [map_translations['EditPolylineCont']], // 'Klikni pro pokračování linie.'
                    end: [map_translations['EditPolylineEnd']] // 'Klikni poslední bod k ukončení linie.'
                }
            },
            rectangle: {
                tooltip: {
                    start: [map_translations['EditRectangleStart']] // 'Pro nakreslení obdělníku klikni a táhni.'
                }
            },
            simpleshape: {
                tooltip: {
                    end: [map_translations['EditSimpleshapeTooltip']] // 'Uvolni kliknutí myši pro dokončení kresby.'
                }
            }
        }
    },
    edit: {
        toolbar: {
            actions: {
                save: {
                    title: [map_translations['ActionsSaveTitle']],
                    text: [map_translations['ActionsSaveText']]
                },
                cancel: {
                    title: [map_translations['ActionsCancelTitle']],
                    text: [map_translations['ActionsCancelText']]
                },
                clearAll: {
                    title: [map_translations['ActionsClearTitle']],
                    text: [map_translations['ActionsClearText']]
                }
            },
            buttons: {
                edit: [map_translations['EditTitle']],
                editDisabled: [map_translations['EditDisabled']], // 'Neexistuje vrstva k editaci'
                remove: [map_translations['RemoveTitle']],
                removeDisabled: [map_translations['RemoveDisabled']] // 'Neexistuje vrstva ke smazání'
            }
        },
        handlers: {
            edit: {
                tooltip: {
                    text: [map_translations['EditTooltipText']], // 'Vyber prvek nebo značku pro editaci.'
                    subtext: [map_translations['EditTooltipSubtext']] // 'Klikni k návratu změn.'
                }
            },
            remove: {
                tooltip: {
                    text: [map_translations['RemoveTooltipText']] // 'Klikni na prvek k odstranění.'
                }
            }
        }
    }
};
L.Draw.Polyline.include({
_createMarker: function (latlng) {
    var marker = new L.Marker(latlng, {
        icon: this.options.icon,
        zIndexOffset: this.options.zIndexOffset * 2
    });
    marker.setOpacity(0.6);
    this._markerGroup.addLayer(marker);

    return marker;
},
}
);
 L.Edit.PolyVerticesEdit.include({

    _createMarker: function (latlng, index) {
		// Extending L.Marker in TouchEvents.js to include touch.
		var marker = new L.Marker.Touch(latlng, {
			draggable: true,
			icon: this.options.icon,
		});
        marker.setOpacity(0.6);
		marker._origLatLng = latlng;
		marker._index = index;

		marker
			.on('dragstart', this._onMarkerDragStart, this)
			.on('drag', this._onMarkerDrag, this)
			.on('dragend', this._fireEdit, this)
			.on('touchmove', this._onTouchMove, this)
			.on('touchend', this._fireEdit, this)
			.on('MSPointerMove', this._onTouchMove, this)
			.on('MSPointerUp', this._fireEdit, this);

		this._markerGroup.addLayer(marker);

		return marker;
	},
});


var drawControl = new L.Control.Draw({
    position: 'topleft',
    draw: {
        polygon: {
            allowIntersection: false, // Restricts shapes to simple polygons
            drawError: {
                color: '#e1e100', // Color the shape will turn when intersects
                message: [map_translations['DrawError']] // '<strong>Oh snap!<strong> you can\'t draw that!' Message that will show when intersect
            },
            shapeOptions: { color: '#ba0d27', },
            icon: new L.DivIcon({
                iconSize: new L.Point(12, 12),
                className: 'leaflet-div-icon leaflet-editing-icon my-own-class'
            })
        },
        // disable toolbar item by setting it to false
        polyline: {
            allowIntersection: false,
            drawError: {
                color: '#e1e100', // Color the shape will turn when intersects
                message: [map_translations['DrawError']] // '<strong>Oh snap!<strong> you can\'t draw that!' Message that will show when intersect
            },
            shapeOptions: { color: '#ba0d27' },
            icon: new L.DivIcon({
                iconSize: new L.Point(12, 12),
                className: 'leaflet-div-icon leaflet-editing-icon my-own-class'
            })
        },
        circle: false, // Turns off this drawing tool
        rectangle: false,
        marker: {
            icon: pinIconRedPoint
        },
        circlemarker: false,
    },
   
    edit: {
        featureGroup: drawnItems, // REQUIRED
        remove: false,
        edit: {
          selectedPathOptions: {
            color: '#ba0d27' ,         
            fillColor: '#fe57a1',       
          }
        },      
        poly: {
          icon: new L.DivIcon({
            iconSize: new L.Point(12, 12),
            className: 'leaflet-div-icon leaflet-editing-icon my-custom-icon'
          }),          
          allowIntersection: false,
         
        }
      }
});


map.addControl(drawControl);

let global_measuring_toolbox = new L.control.measure(
    {
        title: [map_translations['MeasureTitle']],
        icon: '<img src="' + static_url + 'img/ruler-bold-32.png" style="width:20px"/>'
    });
map.addControl(global_measuring_toolbox);

map.addControl(new L.control.coordinates({
    position: "bottomright",
    useDMS:false,
    decimals: 7,
	decimalSeperator: ",",
    labelTemplateLat: "N {y}",
    labelTemplateLng: "E {x}",
    useLatLngOrder: true,
    centerUserCoordinates: true,
    markerType: null
}));
var message_box = L.control.messagebox({ timeout: 10000, position: 'bottomright'}).addTo(map);

function map_show_edit(show, show_go_back) {
    addLogText("arch_z_detail_map.map_show_edit: " + !global_map_can_edit)
    global_map_can_edit = show;
    if (!show) {
        map.removeControl(edit_buttons)
        map.removeControl(drawControl)

        //edit_buttons.disable();

    } else if (show) {
        if (show_go_back) {
            map.addControl(edit_buttons);
        } else {
            map.removeControl(edit_buttons)
        }
        //edit_buttons.enable();
        edit_buttons.disable();//always disable on load
        map.addControl(drawControl);
    }
}

map_show_edit(false)

map.on('contextmenu', (e) => {
    addLogText("arch_z_detail_map.contextmenu")

    var features = [];
    map.contextmenu.removeAllItems();
    map.contextmenu.addItem({ text: [map_translations['MoveFront']], disabled: true }) // 'Přenes do popředí:'
    map.eachLayer(function (layer) {
        if (layer instanceof L.Polyline || layer instanceof L.Polygon) {
            if (layer.getBounds().contains(e.latlng)) {
                features.push(layer.getTooltip().getContent());
                map.contextmenu.addItem({
                    text: layer.getTooltip().getContent(),
                    callback: function () { layer.bringToFront() }
                })
            }
        }
        // do something with the layer
    });
    if (features.length == 0) {
        map.contextmenu.hide();
    } else {
        map.contextmenu.showAt(e.latlng, features)
    }
});

function disableSavePianButton() {
    addLogText("arch_z_detail_map.disableSavePianButton")
    addLogText("disableSavePianButton")
    if (document.getElementById("editPianButton") != null) {
        if (document.getElementById(global_map_element).value === 'undefined') {
            document.getElementById("editPianButton").disabled = true;
            addLogText("disableSavePianButton:disa")
        } else {
            document.getElementById("editPianButton").disabled = false;
            addLogText("disableSavePianButton:enable")
        }
    }
}

map.on('draw:edited', function (e) {
    addLogText("arch_z_detail_map.draw:edited")
    addLogText("edited")
    geomToText();
    save_edited_geometry_session();
});
map.on('draw:deleted', function (e) {
    addLogText("arch_z_detail_map.draw:drawstart")
    addLogText("deleted")
    addWGS84Geometry()
    addSJTSKGeometry()
    disableSavePianButton();
    save_edited_geometry_session();
})

map.on('draw:drawstart', function (e) {
    addLogText("arch_z_detail_map.draw:drawstart")
    if (global_measuring_toolbox._measuring) {
        global_measuring_toolbox._stopMeasuring()
    }
})

map.on('draw:created', function (e) {
    addLogText("arch_z_detail_map.draw:created")
    if (global_map_can_edit) {
        var type = e.layerType;
        var la = e.layer;

        if (type === 'marker') {
            drawnItems.clearLayers();

            let x2 = e.layer._latlng.lat;
            let x1 = e.layer._latlng.lng;
            if (global_map_can_edit) {
                //odebrano [map_translations['TempPIAN']])
                L.marker([x2, x1], { icon: pinIconRedPoint }).bindTooltip(map_translations['TempPIAN']).addTo(drawnItems); //'Navržený pian' aaaa
            }
        } else {
            drawnItems.clearLayers();
            //gm_correct.clearLayers();
            drawnItems.addLayer(la);
        }
        addLogText("created")
        geomToText();
        save_edited_geometry_session();
        disableSavePianButton();

    }
});


//převod geometrie pianu do textoveho formatu posílaného na server
function geomToText() {//Desc: This fce moves edited geometry into HTML element
    addLogText("arch_z_detail_map.geomToText")
    // LINESTRING(-71.160281 42.258729,-71.160837
    // POLYGON((-71.1776585052917 42.3902909739571,-71.177682
    // POINT(-71.064544 42.28787)');
    var text = "";
    var jtsk_text = ""
    var jtsk_coor = []
    let coordinates = [];
    drawnItems.eachLayer(function (layer) {
        if (layer instanceof L.Marker) {
            addLogText('im an instance of L point');
            let latlngs = layer.getLatLng()
            text = "POINT(" + latlngs.lng + " " + latlngs.lat + ")"
            jtsk_coor = convertToJTSK(latlngs.lng, latlngs.lat);
            jtsk_text = "POINT(" + jtsk_coor[0] + " " + jtsk_coor[1] + ")"
            //coordinates.push([latlngs.lng, latlngs.lat])
        }
        else if (layer instanceof L.Polygon) {
            addLogText('im an instance of L polygon');
            text = "POLYGON(("
            jtsk_text = "POLYGON(("
            let latlngs = layer.getLatLngs()
            for (var i = 0; i < latlngs.length; i++) {
                for (var j = 0; j < latlngs[i].length; j++) {
                    coordinates.push([latlngs[i][j].lng, latlngs[i][j].lat])
                    text += (latlngs[i][j].lng + " " + latlngs[i][j].lat) + ",";
                    jtsk_coor = convertToJTSK(latlngs[i][j].lng, latlngs[i][j].lat);
                    jtsk_text += (jtsk_coor[0] + " " + jtsk_coor[1]) + ",";
                }
            }
            // Musi koncit na zacatek
            text += coordinates[0][0] + " " + coordinates[0][1]
            text += "))"
            jtsk_coor = convertToJTSK(coordinates[0][0], coordinates[0][1]);
            jtsk_text += jtsk_coor[0] + " " + jtsk_coor[1]
            jtsk_text += "))"
        }
        else if (layer instanceof L.Polyline) {
            addLogText('im an instance of L polyline');
            text = "LINESTRING("
            jtsk_text = "LINESTRING("
            let it = 0;
            coordinates = layer.getLatLngs()
            for (let i in coordinates) {
                if (it > 0) { text += ","; jtsk_text += ","; }

                it++;
                text += (coordinates[i].lng + " " + coordinates[i].lat);
                jtsk_coor = convertToJTSK(coordinates[i].lng, coordinates[i].lat);
                jtsk_text += (jtsk_coor[0] + " " + jtsk_coor[1]);
            }
            text += ")"
            jtsk_text += ")"
        }
        addWGS84Geometry(amcr_static_geom_precision_wgs84(text), global_map_can_edit);
        addSJTSKGeometry(amcr_static_geom_precision_jtsk(jtsk_text), global_map_can_edit);
    });



}

//zobrazení DJ které daný pian obsahují
function onMarkerClick(ident_cely,e) {
    addLogText("arch_z_detail_map.onMarkerClick")
    const popup = e.target.getPopup();
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
            try{
                let link='<a href="/id/' + i.dj + '" target="_blank">' + i.dj + '</a></br>'
                text = text + link
            } catch(e){
                addLogText("err:"+e)
            }
        })
        if(text=="") text="--"
        popup.setContent(text);
    }
 }

var clickOnMap=(e)=>{
    addLogText("arch_z_detail_map.clickOnMap")
    if(!global_map_can_grab_geom_from_map){
       
        if(global_unwanted_popup){
            global_unwanted_popup.unbindPopup()
            global_unwanted_popup=null
        }
        if(typeof e.target.bindPopup === 'function'){ 
            e.target.bindPopup("").openPopup();
            global_unwanted_popup=e.target
            onMarkerClick(e.target.getTooltip().getContent().split(" ")[0],e)
            var features = 0;
            map.eachLayer(function (layer) {
                if (layer instanceof L.Polyline || layer instanceof L.Polygon) {
                    if (layer.getBounds().contains(e.latlng)) {
                        features =features+1;
                    }
                }
            });
            if (features>1) {
                message_box.show( map_translations['MessageMultipleElements'] );
                message_box.timeStamp=e.originalEvent.timeStamp;
                
            }
            else message_box.hide()
        }
      
     
    }

}

map.on('click', function (e) {
    clickOnMap(e);
   if(message_box.timeStamp!=e.originalEvent.timeStamp) message_box.hide()
  
});

map.on('overlayadd', function(eventlayer){
    if(eventlayer.layer===poi_sn || eventlayer.layer===poi_all){
        switchMap(false)
    }
});

map.on('overlayremove', function(eventlayer){
    if(eventlayer.layer===poi_sn || eventlayer.layer===poi_all){
        switchMap(false)
    }
});


var mouseOverGeometry =(geom, allowClick=true)=>{
    function getContent(e){
        let content="";
        try{
            content = e.target.getPopup().getContent();
        }catch(ee){
            content = e.target.getTooltip().getContent();
        }
        return content;
    }

    if(allowClick){
        geom.on('click', function (e) {
            if(global_unwanted_popup){
                global_unwanted_popup.unbindPopup()
                global_unwanted_popup=null
            }
            if(global_measuring_toolbox._measuring){
                global_measuring_toolbox._stopMeasuring()
            }
            //pian připnout z mapy
            if(global_map_can_grab_geom_from_map!==false && !global_map_can_edit ){
                map.spin(false);
                map.spin(true);
                $.ajax({
                    type: "GET",
                    url:"/pian/autocomplete/?q="+getContent(e).split(" ")[0],
                    dataType: 'json',
                    success: function(data){
                        if(data.results.length>0){
                        $('#id_'+global_map_can_grab_geom_from_map+'-pian').select2("trigger", "select",{data:data.results[0]})
                        }
                        map.spin(false);
                        set_pian_by_id(global_map_can_grab_geom_from_map)
                        },
                    error: ()=>{
                    // global_map_can_grab_geom_from_map=false;
                    }
                })
            } else{
                clickOnMap(e);
            }
        })
    }
    if(geom.options.icon) geom.options.iconOld=geom.options.icon;
    if(geom.options.color)geom.options.colorOld=geom.options.color;
    geom.on('mouseover', function() {
        if(!global_map_can_edit){
            if (geom instanceof L.Marker){                
                if(this.options.changeIcon){
                    this.setIcon(pinIconYellowHW);
                    if(this.polyline) this.polyline.setStyle({color: 'gold'});
                  
                }else{
                    this.setIcon(pinIconYellowPoint);
                }
            } else {                
                this.setStyle({color: 'gold'});
                if(this.marker) this.marker.setIcon(pinIconYellowHW);               
            }
        }
    });

    geom.on('mouseout', function() {
        if(!global_map_can_edit){
            if (geom instanceof L.Marker){
                this.setIcon(this.options.iconOld);
                if(this.polyline) this.polyline.setStyle({color:this.polyline.options.colorOld});

            } else {
                this.setStyle({color:this.options.colorOld});
                if(this.marker)this.marker.setIcon(this.marker.options.iconOld);
            }
        }
    })
}

//vykreslení pianů vybrané DJ
const addDJPian = (geom, layer, pian_ident_cely, st_text, presnost,color,DJ_ident_cely) => {
    addLogText("arch_z_detail_map.addDJPian")
    if(color=="gold") {
        //gold_pian_ident_cely=pian_ident_cely;        
        pinDefBod={ icon: pinIconYellowHW, zIndexOffset: 2000 ,changeIcon: true }; 
        pinBod={ icon: pinIconYellowPoint, zIndexOffset: 2000 }; 
    }
    else {
        pinDefBod={ icon: pinIconGreenHW, zIndexOffset: 1000 ,changeIcon: true}; 
        pinBod={ icon: pinIconGreenPoint, zIndexOffset: 1000 };
    }
    let coor = []
    //akce_ident_cely = document.getElementById("id-app-entity-item").textContent.trim().split("Zpět")[0]
    //let link='<a href="/arch-z/akce/detail/'+akce_ident_cely+'/dj/'+text+'" target="_blank">'+text+'</a></br>'
    
    if (st_text.includes("POLYGON") || st_text.includes("LINESTRING")) {
        //ToDo" 21.06.2022 pinIconYellow
        var polyline;
        var marker=L.marker(amcr_static_coordinate_precision_wgs84(geom), pinDefBod,presnost!=4)
        mouseOverGeometry(marker
        .bindTooltip(pian_ident_cely+' ('+presnost+')', { sticky: true },presnost!=4)
        .bindPopup('')
        .addTo(layer));
        if (st_text.includes("POLYGON")) {
            st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
                coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0].replace("(","")]));
            })
            polyline=L.polygon(coor, { color: color });
            mouseOverGeometry(polyline
            .bindTooltip(pian_ident_cely+' ('+presnost+')', { sticky: true },presnost!=4)
            .addTo(layer));
        } else if (st_text.includes("LINESTRING")) {
            st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
                coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]))
            })
            polyline=L.polyline(coor, { color: color });
            mouseOverGeometry(polyline
            .bindTooltip(pian_ident_cely+' ('+presnost+')', { sticky: true },presnost!=4)
            .addTo(layer));
        }
        polyline.marker= marker;
        marker.polyline=polyline;
        
        $( "#el_div_dokumentacni_jednotka_"+DJ_ident_cely )
        .on( "mouseenter", function() {       
            polyline.fire("mouseover");
        } )
        .on( "mouseleave", function() {
            polyline.fire("mouseout");
        } );
    } else {  
        var marker=L.marker(amcr_static_coordinate_precision_wgs84(geom),pinBod,presnost!=4)    
        mouseOverGeometry(marker
        .bindTooltip(pian_ident_cely+' ('+presnost+')', { sticky: true })
        .bindPopup('')
        .addTo(layer));
        coor.push(geom);
        $("#el_div_dokumentacni_jednotka_"+DJ_ident_cely)
        .on( "mouseenter", function() {       
            marker.fire("mouseover");
        } )
        .on( "mouseleave", function() {
            marker.fire("mouseout");
        } );
    }
    
    return coor;
}

//vykreslení pianů vybrané DJ 
const addPointQuery = (geom, layer, ident_cely, st_text, presnost, popup_text) => {
    addLogText("arch_z_detail_map.addPointQuery")
    let coor = []
    if (st_text.includes("POLYGON") || st_text.includes("LINESTRING")) {
        if (st_text.includes("POLYGON")) {
            st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
                str_coord = i.trim().split(" ");
                coor.push(amcr_static_coordinate_precision_wgs84([str_coord[1], str_coord[0]]));
            })
            mouseOverGeometry(L.polygon(coor, { color: 'gold' })
            .bindTooltip(ident_cely, { sticky: true },presnost!=4)
            .bindPopup(popup_text)
            .addTo(layer));
        } else if (st_text.includes("LINESTRING")) {
            st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
                str_coord = i.trim().split(" ");
                coor.push(amcr_static_coordinate_precision_wgs84([str_coord[1], str_coord[0]]))
            })
            mouseOverGeometry(L.polyline(coor, { color: 'gold' })
            .bindTooltip(ident_cely, { sticky: true },presnost!=4)
            .bindPopup(popup_text)
            .addTo(layer));
        }
    } else {
        i=st_text.split("(")[1].split(")")[0]
        coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1].trim(), i.split(" ")[0].trim()]));
        mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84(coor[0]), { icon: presnost!=4 ? pinIconYellowPoint: pinIconYellowHW, zIndexOffset: 2000,changeIcon: presnost==4 },presnost!=4)
        .bindTooltip(ident_cely, { sticky: true },presnost!=4)
        .bindPopup(popup_text)
        .addTo(layer));
    }
    //map.setView(coor[0],17)

}

//vykreslení ostatních pianů
var addPointToPoiLayer = (st_text, layer, text, overview = false, presnost) => {
    addLogText("arch_z_detail_map.addPointToPoiLayer")
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
        mouseOverGeometry(L.polygon(coor, myColor)
        .bindTooltip(text+' ('+presnost+')', { sticky: true })
        .addTo(layer),presnost!=4);
    } else if (st_text.includes("LINESTRING")) {
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]))
        })
        mouseOverGeometry(L.polyline(coor, myColor)
        .bindTooltip(text+' ('+presnost+')', { sticky: true })
        .addTo(layer),presnost!=4);
    } else if (st_text.includes("POINT")) {
        let i = st_text.split("(")[1].split(")")[0];
        coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]))
        if (layer === poi_pian) {
            mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]), myIco)
            .bindTooltip(text+' ('+presnost+')')
            .addTo(layer),presnost!=4);
        }

    }
    if (overview && coor.length > 0 && layer !== poi_pian) { //ToDo: vypnout def. body && layer!==poi_pian)
        if (layer === poi_pian) {
            layer = poi_pian_dp;
        }
        x0 = 0.0;
        x1 = 0.0
        c0 = 0
        //addLogText(coor)
        for (const i of coor) {
            if(!(st_text.includes("POLYGON") && c0==coor.length-1)){
                x0 = x0 + parseFloat(i[0])
                x1 = x1 + parseFloat(i[1])
                c0 = c0 + 1
            }
        }
        if (st_text.includes("POLYGON") || st_text.includes("LINESTRING")) {
            mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84([x0 / c0, x1 / c0]), myIco2)
            .bindTooltip(text+' ('+presnost+')')
            .addTo(layer));
        } else {
            mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84([x0 / c0, x1 / c0]), myIco)
            .bindTooltip(text+' ('+presnost+')')
            .addTo(layer));
        }

    }
    //heatPoints.push()
    drawnItems.bringToFront();
}

function addLogText(text) {
    //console.log(text)
}

function addWGS84Geometry(text) {
    addLogText("arch_z_detail_map.addWGS84Geometry: " + global_map_element + " " + text)
    let geom = document.getElementById(global_map_element);
    if (geom) {
        geom.value = text;
    }
    if (poi_sugest.getLayers().size) {
        edit_buttons.enable();
    }
}

function addSJTSKGeometry(text) {
    addLogText("arch_z_detail_map.addSJTSKGeometry: " + global_map_element_sjtsk + " " + text)
    let geom_sjtsk = document.getElementById(global_map_element_sjtsk);
    if (geom_sjtsk) {
        geom_sjtsk.value = text;
    }
    if (poi_sugest.getLayers().size) {
        edit_buttons.enable();
    }
}

function clearUnfinishedEditGeometry() {
    addLogText("arch_z_detail_map.clearUnfinishedEditGeometry")
    global_map_element = "id_geom";
    global_map_element_sjtsk = "id_geom_sjtsk";
    addLogText("zmena def.geom :" + global_map_element)
    global_map_can_grab_geom_from_map = false;
    map_show_edit(false, false)
    drawnItems.clearLayers();
    drawnItemsBuffer.eachLayer(function (layer) {
        layer.addTo(poi_dj)
    })

}

//nepoužito
function loadGeomToEdit(ident_cely) {
    addLogText("arch_z_detail_map.loadGeomToEdit")
    drawnItems.clearLayers();
    drawnItemsBuffer.clearLayers();
    let drawnItemsCount = 0;
    let layerColor = "green";
    let PolylineColor = '#ba0d27';
    let PolygonColor = '#ba0d27';
    map.eachLayer(function (layer) {
        if (layer instanceof L.Polyline || layer instanceof L.Polygon || layer instanceof L.Marker) {
            let content = "";
            try {
                content = layer.getPopup().getContent();
            } catch (ee) {
                try {
                    content = layer.getTooltip().getContent();
                } catch (eee) {
                    // addLogText(layer)
                }
            }
            if (content == ident_cely) {
                drawnItemsCount = drawnItemsCount + 1;
                if (layer instanceof L.Marker) {
                    let latlngs = layer.getLatLng()
                    if (drawnItemsCount == 1) {
                        layer.setIcon(pinIconRedPoint);
                        layer.unbindTooltip();
                        layer.addTo(drawnItems);
                        //UNDO-layer-start
                        L.marker(amcr_static_coordinate_precision_wgs84([latlngs.lat, latlngs.lng]), { icon: pinIconRedPoint }).bindPopup(content).addTo(drawnItemsBuffer);
                        //UNDO-layer-end
                    } else {
                        layer.remove();
                    }
                } else if (layer instanceof L.Polygon) {
                    if (drawnItemsCount > 1) {
                        drawnItems.clearLayers();
                    }
                    layerColor = layer.options.color;
                    layer.setStyle({ color: PolygonColor });
                    layer.addTo(drawnItems);
                    //UNDO-layer-start
                    let latlngs = layer.getLatLngs()
                    let coordinates = [];
                    for (var i = 0; i < latlngs.length; i++) {
                        for (var j = 0; j < latlngs[i].length; j++) {
                            coordinates.push(amcr_static_coordinate_precision_wgs84([latlngs[i][j].lat, latlngs[i][j].lng]))
                        }
                    }
                    L.polygon(coordinates, { color: layerColor }).bindTooltip(content, { sticky: true }).addTo(drawnItemsBuffer);
                    //UNDO-layer-end
                } else if (layer instanceof L.Polyline) {
                    if (drawnItemsCount > 1) {
                        drawnItems.clearLayers();
                    }
                    layerColor = layer.options.color;
                    layer.setStyle({ color: PolylineColor });
                    layer.addTo(drawnItems);
                    //UNDO-layer-start
                    let latlngs = layer.getLatLngs()
                    let coordinates = [];
                    for (let i in latlngs) {
                        coordinates.push(amcr_static_coordinate_precision_wgs84([latlngs[i].lat, latlngs[i].lng]));
                    }
                    L.polyline(coordinates, { color: layerColor }).bindTooltip(content, { sticky: true }).addTo(drawnItemsBuffer);
                    //UNDO-layer-end
                }
            }
        }
    })
    if (drawnItemsCount) {

        global_map_element = "id_" + ident_cely + "-geom"
        global_map_element_sjtsk = "id_" + ident_cely + "-geom_sjtsk"
        addLogText("zmena def.geom :" + global_map_element)
        geomToText();
        drawControl._toolbars.edit._modes.edit.handler.enable();
    } else {
        addLogText("zmena def.geom :chyba")
    }

}

//switchMap ();
var boundsLock = 0;

//map.on('zoomend', function() {
//    addLogText("zoomed")
//    switchMap(true)
//});



map.on('moveend', function () {
    addLogText("drzim def.geom :" + global_map_element)
    //addLogText(ident_cely)
    addLogText("arch_z_detail_map.moveend")
    switchMap(false)
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

//překreslení mapy
switchMap = function (overview = false) {
    var bounds = map.getBounds();
    let zoom = map.getZoom();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();
    const currentUrl = window.location.href;
    if (global_map_can_load_pians && (map.hasLayer(poi_all) || map.hasLayer(poi_sn))) {
        if (overview || bounds.northWest != boundsLock.northWest || !boundsLock.northWest) {
            addLogText("Change: " + northWest + "  " + southEast + " " + zoom);
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
                    'pian':map.hasLayer(poi_all),
                    'pas':map.hasLayer(poi_sn),
                }));

            xhr.onload = function () {
                try{
                    poi_sn.clearLayers();
                    poi_pian.clearLayers();
                    poi_pian_dp.clearLayers();
                    heatPoints = []
                    map.removeLayer(heatLayer);
                    if (JSON.parse(this.responseText).algorithm == "detail") {
                        let resPoints = JSON.parse(this.responseText).points
                        var count = JSON.parse(this.responseText).count;                       
                        resPoints.forEach((i) => {

                            if(i.type=="pas"){
                                let ge = i.geom.split("(")[1].split(")")[0];
                                L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconPurplePin })
                                .bindTooltip(i.ident_cely, { sticky: true })
                                .bindPopup('<a href="/pas/detail/'+i.ident_cely+'" target="_blank">'+i.ident_cely+'</a>')
                                .addTo(poi_sn)
                            } else if(i.type=="pian"){
                                try{
                                    
                                    if(DJ_pians_ident_cely.indexOf(i.ident_cely) == -1){
                                        if (count<500) {
                                            addPointToPoiLayer(i.geom, poi_pian, i.ident_cely, true,i.presnost)
                                        } else {
                                            addPointToPoiLayer(i.centroid, poi_pian_dp, i.ident_cely, true,i.presnost)
                                        }
                                    }
                                }catch(e){
                                    addLogText("err2: "+e)
                                }
                            }
                        })
                        /*if (count > 50 && count<500) {
                            map.removeLayer(poi_pian_dp);
                        } else if (!map.hasLayer(poi_pian_dp)) {
                           // map.addLayer(poi_pian_dp);
                        }*/
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
                        //addLogText({max:maxHeat,data:heatPoints})
                        heatLayer.setData({max:maxHeat,data:heatPoints})
                        map.addLayer(heatLayer);
                        poi_pian.clearLayers();
                        poi_pian_dp.clearLayers();
                    }
                    map.spin(false);
                } catch(e){map.spin(false);addLogText(e)}
            };
        }
    } else if(!map.hasLayer(poi_all) && !map.hasLayer(poi_sn)){
        map.removeLayer(heatLayer);
    }
}

function loadKatastry() {
    addLogText("arch_z_detail_map.loadKatastry")
    akce_ident_cely = document.getElementById("id-app-entity-item").textContent.trim().split("Zpět")[0]
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/arch-z/mapa-dalsi-katastry');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    } else {
        addLogText("neni X-CSRFToken token")
    }
    xhr.onload = function () {
        rs = JSON.parse(this.responseText)
        let hlavni_katastr = ""
        let ostatni_katastry = [];
        global_map_katastry_all = rs;
        for (var i = 0; i < rs.points.length; i++) {
            if (i == 0) {
                hlavni_katastr = rs.points[i].dj_katastr;
            } else if (hlavni_katastr != rs.points[i].dj_katastr) {
                ostatni_katastry.push(rs.points[i].dj_katastr)
            }
        }
        ostatni_katastry = [...new Set(ostatni_katastry)].sort();
        //addLogText("HL:"+hlavni_katastr);
        //addLogText("OST:"+ostatni_katastry);
        document.getElementById("main_cadastre_id").value = hlavni_katastr;
        document.getElementById("other_cadastre_id").value = ostatni_katastry.join(", ");
    };
    xhr.send(JSON.stringify(
        {
            'akce_ident_cely': akce_ident_cely,
        }));

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

//loadKatastry();
//funkce vyhledávání v mapě
function searchByAjax(text, callResponse) {
    addLogText("arch_z_detail_map.searchByAjax")
    let items1 = [];
    let items2 = [];

    let ajaxCall = [
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
            data: { text: text },
            dataType: 'json',
            success: function (json) { items2 = json.suggestions.sort( compareSearchResult );/*addLogText("Vyhledany Okresy");*/ }
        }),

    ];
    Promise.all(ajaxCall).then(() => {/*addLogText("Vyhledani ukonceno");*/callResponse([...items2, ...items1]); })
}

//uložení editované geometrie do session pro případnou opravu
function save_edited_geometry_session(){
    addLogText("arch_z_detail_map.save_edited_geometry_session")
    const currentUrl = window.location.href;
     sessionStorage.setItem("Geom-session",JSON.stringify({url:currentUrl,geometry:document.getElementById(global_map_element).value}))
}

function checkBlockedByQWuery(){
    addLogText("arch_z_detail_map.checkBlockedByQWuery")
    const currentUrl = window.location.href;
    const urlParams = new URLSearchParams(window.location.search);
    let myParamG = urlParams.get('geometry');
    if(myParamG !==null){
        return true
    }
    return false;
}

window.addEventListener("load", function(){
    if( global_map_can_edit==true) {
        loadSession();
        geomToText();
        save_edited_geometry_session()
    } 
    else{
        sessionStorage.removeItem("Geom-session");
    }
});


//nahrání geometrie dočasně uložené v session
function loadSession(){
    addLogText("arch_z_detail_map.loadSession")
    const currentUrl = window.location.href;
    const urlParams = new URLSearchParams(window.location.search);
    //global_map_can_grab_geom_from_map = true;
    if(typeof geom !== 'undefined' && geom.geometry !==''){
        global_map_can_grab_geom_from_map = true;
        global_blocked_by_query_geom=true;
        drawnItems.clearLayers();
        drawnItemsBuffer.clearLayers();
        addPointQuery(null,  drawnItems,geom.label,geom.geometry,false, map_translations.currentlyEditedPian);
        geomToText();
        save_edited_geometry_session()
        map.fitBounds(drawnItems.getBounds());
        //myParam="POINT (13.2164736 49.9596986)"
        //http://localhost:8000/arch-z/akce/detail/C-202211987A/dj/C-202211987A-D02?geometry=
        //myParam="POLYGON ((13.2164736 49.9596986,13.2154006 49.9589111,13.2178685 49.9583378,13.2183513 49.9593602,13.2164736 49.9596986))"
        //myParam="POLYGON ((13.2164736 49.9596986,13.2154006 49.9589111,13.2178685 49.9583378,13.2165204 49.9590543,13.2164736 49.9596986))"
    } else{
        let geom_session=sessionStorage.getItem("Geom-session")
        if(geom_session != null){
            geom_session=JSON.parse(geom_session)
            if(geom_session.url==currentUrl && geom_session.geometry !=null){
                global_blocked_by_query_geom=true;
                global_map_can_edit=true;
                map_show_edit(global_map_can_edit);
                drawnItems.clearLayers();
                drawnItemsBuffer.clearLayers();
                //POLYGON ((13.2496364 50.0099953, 13.2502051 50.0099539, 13.2500978 50.0094364, 13.2496364 50.0099953))
                //POLYGON ((13.2491214 50.0100783, 13.2482845 50.0096987, 13.249218 50.0096021, 13.2491214 50.0100783))
                //POLYGON((13.2496364 50.0099953, 13.2502051 50.0099539, 13.2500978 50.0094364, 13.2496364 50.0099953))
                //myParam="POLYGON((13.2496364 50.0099953,13.2502051 50.0099539,13.2500978 50.0094364,13.2496364 50.0099953))"
                addPointQuery(null,  drawnItems,map_translations.currentlyEditedPian,geom_session.geometry,false,
                    map_translations.currentlyEditedPian);
                geomToText();
                map.fitBounds(drawnItems.getBounds());
                //map.setView(drawnItems,17)

            }else{
                sessionStorage.setItem("Geom-session",JSON.stringify({url:currentUrl,geometry:null}));
            }
        }
    }
}

//zobrazení pianů akce a zoom na ně
function arch_select_perspective(currentUrl,selected_ku,selected_ident_cely,selected_dj){
    addLogText("show Choose: "+currentUrl+" "+selected_ku+ " "+selected_ident_cely+" <"+selected_dj+">")

    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/arch-z/mapa-zoom');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
    } else {
        addLogText("neni X-CSRFToken token")
    }
    xhr.onload = function () {
        const rs = JSON.parse(this.responseText);
        if (rs.count==0 ){
            switchMap(false);
            return;
        }                 
        poi_dj.clearLayers();
        if(global_blocked_by_query_geom==false) drawnItems.clearLayers();        
        zoomed=false;
        rs.pians.forEach((pian) => {
                DJ_pians_ident_cely.push(pian.pian_ident_cely);
                var layer = poi_dj ;
                if(pian.color=="gold" && global_map_can_edit == true) layer = drawnItems;
                if(global_blocked_by_query_geom==false && pian.hasOwnProperty("DJ_ident_cely")) {                       
                    coor=addDJPian([pian.lat, pian.lng],  layer,pian.pian_ident_cely,pian.geom,pian.presnost,pian.color,pian.DJ_ident_cely);
                }
                if(pian.color=="gold" && pian.zoom!=12 && global_blocked_by_query_geom==false){
                    bbox=L.polyline(coor).getBounds()
                    viewParam=map._getBoundsCenterZoom(bbox);
                    if(map.getMaxZoom()==viewParam.zoom) map.setView(viewParam.center, 18)    ;                
                    else map.setView(viewParam.center, viewParam.zoom) ;  
                    zoomed=true;                 
                }
        })
        if(zoomed==false && global_blocked_by_query_geom==false){
            zoom_pian=rs.pians.find((element) => element.color=='gold' )
            if(zoom_pian==undefined)zoom_pian=rs.pians.find((element) => element.zoom!=12)
            if(zoom_pian==undefined)zoom_pian= rs.pians[0];
            if(zoom_pian.zoom==12){
                    if(zoom_pian.bbox!=""){
                        box=[]
                        zoom_pian.bbox.split("((")[1].split(")")[0].split(",").forEach(i => {                          
                            box.push([i.split(" ")[1].trim(), i.split(" ")[0].trim()]);
                        })
                        //latLng(40.712, -74.227),
                        map.fitBounds([ [box[0][0],box[0][1] ],[box[2][0],box[2][1] ]]);
                    }
                    else map.setView([zoom_pian.lat, zoom_pian.lng], zoom_pian.zoom)
            }
            else{
                viewParam=map._getBoundsCenterZoom(poi_dj.getBounds() )
                if(map.getMaxZoom()==viewParam.zoom) map.setView(viewParam.center, 18)                    
                else map.setView(viewParam.center, viewParam.zoom) ;  
               // map.setView([zoom_pian.lat, zoom_pian.lng], zoom_pian.zoom)
            } 
        } 

    } ;

    selected_dj=selected_dj.trim();

    if(selected_dj!='')ident=selected_dj;
    else ident=selected_ident_cely
    xhr.send(JSON.stringify(
        {
            'cadastre': selected_ku,
            'akce_ident_cely':ident,
        }))

}


//Lokalizace projektu
window.addEventListener("load", (event) => {
    addLogText("arch_z_detail_map.load")
    let xhr_proj = new XMLHttpRequest();
    xhr_proj.open('POST', '/projekt/akce-get-projekt');
    if (typeof global_csrftoken !== 'undefined') {
        xhr_proj.setRequestHeader('X-CSRFToken', global_csrftoken);

    }
    map.spin(false);
    map.spin(true);
    xhr_proj.send(JSON.stringify(
        {
            'projekt_ident_cely': global_map_projekt_ident,
        }));
    xhr_proj.onload = function () {
        poi_model.clearLayers();
        let resPoints = JSON.parse(this.responseText).points
        if(resPoints.length==0)control.removeLayer(poi_model);
        resPoints.forEach((i) => {
            try{
                let ge = i.geom.split("(")[1].split(")")[0];
                L.marker(amcr_static_coordinate_precision_wgs84([ge.split(" ")[1], ge.split(" ")[0]]), { icon: pinIconGreenPin })
                .bindPopup(i.ident_cely)
                .addTo(poi_model)
            } catch(e){
                control.removeLayer(poi_model);
                addLogText("Projekt nema geometrii")
            }
        })
        map.spin(false);
    }


});
