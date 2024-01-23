var global_map_can_edit=true;
//https://github.com/pointhi/leaflet-color-markers
var greenIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
    })

    var redIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
    })


var osmColor = L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM map', maxZoom: 19.99, minZoom: 6 }),
    cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/ortofoto_wm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom: 19.99, minZoom: 6 }),
    cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 20, minZoom: 6 }),
    cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/zmwm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 19.99, minZoom: 6 });


var poi_sugest = L.layerGroup();
var gm_correct = L.layerGroup();
var poi_other = L.markerClusterGroup({disableClusteringAtZoom:20});//L.layerGroup();

var map = L.map('projectMap',{zoomControl:false,  layers: [osmColor]}).setView([49.84, 15.17], 7);




var baseLayers = {
        [map_translations['openStreetMap']]: osmColor,
        [map_translations['cuzkzakladniMapyCr']]: cuzkZM,
        [map_translations['cuzkOrtofotomapa']]: cuzkOrt,
        [map_translations['cuzkStinovanyeelief5G']]: cuzkEL,
    };

var overlays ={
    [map_translations['cuzkKatastralniMapa']]:  L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 20.99, minZoom: 17, opacity: 0.5 }),
    [map_translations['cuzkKatastralniUzemi']]: L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom: 20.99, minZoom: 12, opacity: 0.5 })
}

L.control.layers(baseLayers,overlays).addTo(map);
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

    var buttons = [
L.easyButton({
        states: [{
            stateName: 'add-lock',
            icon: 'bi-lock',
            title: [map_translations['EditTurnOff']],
            onClick: function(control) {
                global_map_can_edit=!global_map_can_edit;
                //toggleMarkerButton(false);
                console.log("zamknout");
                map.removeControl(drawControl)
                //drawControl.removeToolbar();
                control.state('remove-lock');
            }
            }, {
            icon: 'bi bi-pencil',
            stateName: 'remove-lock',
            title: [map_translations['EditTurnOn']],
            onClick: function(control) {
                global_map_can_edit=!global_map_can_edit;
                //toggleMarkerButton(true);
                map.addControl(drawControl);
                console.log("odemknout")
                control.state('add-lock');
            }
            }]
    }),

L.easyButton( 'i bi-skip-backward-fill', function(){
        //gm_correct.clearLayers();
        //editableLayers.clearLayers();
        map.setView(poi_sugest.getLayers()[0]._latlng, 18);
    }, [map_translations['DefaultTitle']])]


L.easyBar(buttons).addTo(map);
//var editableLayers = new L.FeatureGroup();
//map.addLayer(editableLayers);

/*function toggleMarkerButton(state) {
    // toggle button dimming and clickability
    var button = document.getElementsByClassName("leaflet-draw-draw-marker")[0];
    if (state) {
        // enable button
        button.onClick = null;
        button.className = "leaflet-draw-draw-marker leaflet-draw-toolbar-button-enabled";
    } else {
        // disable button
        button.onClick = "preventEventDefault(); return false";
        button.className = "leaflet-draw-draw-marker draw-control-disabled";
    }
}*/
var editableLayers = new L.FeatureGroup();
map.addLayer(editableLayers);
var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

L.drawLocal = {
    // format: {
    // 	numeric: {
    // 		delimiters: {
    // 			thousands: ',',
    // 			decimal: '.'
    // 		}
    // 	}
    // },
    draw: {
        toolbar: {
            // #TODO: this should be reorganized where actions are nested in actions
            // ex: actions.undo  or actions.cancel
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



var drawControl = new L.Control.Draw( {
    position: 'topleft',
    draw: {
        polygon: {
        allowIntersection: false, // Restricts shapes to simple polygons
        drawError: {
            color: '#e1e100', // Color the shape will turn when intersects
            message: [map_translations['DrawError']] // '<strong>Oh snap!<strong> you can\'t draw that!' Message that will show when intersect
        },
        shapeOptions: {
            color: '#97009c'
        }
        },
        // disable toolbar item by setting it to false
        polyline: {
        shapeOptions: {color: '#662d91' }
        },
        circle: false, // Turns off this drawing tool
        rectangle: false,
        marker: {
            icon: redIcon
        },
        circlemarker: false,
        },
    edit: {
        featureGroup: drawnItems, //REQUIRED!!
        remove: true
    }
    });


map.addControl(drawControl);

L.control.measure().addTo(map)

map.addControl(new L.control.coordinates({
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


map.on('draw:edited', function (e) {
    var layers = e.layers;
    var countOfEditedLayers = 0;
    layers.eachLayer(function(layer) {
        countOfEditedLayers++;
    });
    console.log("Edited " + countOfEditedLayers + " layers");
});

map.on('draw:created', function(e) {
if(global_map_can_edit){
    var type = e.layerType;
    var la = e.layer;
    console.log(e)


    if (type === 'marker'){
        drawnItems.clearLayers();

        let corX = e.layer._latlng.lat;
        let corY = e.layer._latlng.lng;
        addPointToPoiLayer(corX, corY, [map_translations['lokalizaceZamer']], la);  // 'Vámi vybraná poloha záměru'
    } else{
        drawnItems.clearLayers();
        //gm_correct.clearLayers();
        drawnItems.addLayer(la);
    }

}
});

map.addLayer(poi_sugest);
map.addLayer(poi_other);


//adding other points to layer
var getOtherPoi= ()=>{
    poi_other.clearLayers();
//                console.log('delka vsech:'+points.length)

    points.forEach((point) => {
        if(map.getBounds().getEast()> point[1] &&  point[1]> map.getBounds().getWest()
        &&
        map.getBounds().getSouth()< point[0] &&  point[0]< map.getBounds().getNorth()
        ){
//            pp.push(point[0])
            if(point.length>2){
                L.marker([point[0],point[1]]).bindPopup(point[2]).addTo(poi_other)
            } else {
                L.marker([point[0],point[1]]).addTo(poi_other)
            }

        }
    });
//               console.log('delka vybranych: '+pp.length)
}

var addPointToPoiLayer = (lat, long, text,lai) => {
    if( global_map_can_edit){
        L.marker([lat, long], {icon: redIcon}).bindPopup(text).addTo(drawnItems);
        //console.log(lat+'  '+ long)
    }
}
var addPointOnLoad = (lat, long, text) => {
    if(text){
        L.marker([lat, long], {icon: greenIcon}).bindPopup(text).addTo(poi_sugest);
    } else{
        L.marker([lat, long], {icon: greenIcon}).addTo(poi_sugest);
    }

    map.setView([lat, long], 18)
    getOtherPoi();
}

addPointOnLoad(50.28702571184197,14.830008745193483, [map_translations['lokalizaceZamer']]);  // "Uživatelem zadaná poloha záměru"

map.on('zoomend', function() {
    //console.log(map.getZoom())
    if (map.getZoom() > 5) {
        getOtherPoi();
    }
});

map.on('click', function (e) {
        //console.log("Your zoom is: "+map.getZoom())
        //var type = e.layerType;
        //console.log("Your type: "+type)
        //console.log(e)
        //console.log(map.getBounds())

});
