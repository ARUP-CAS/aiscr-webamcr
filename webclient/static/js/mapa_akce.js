var global_map_can_edit=true;
//https://github.com/pointhi/leaflet-color-markers
var greenIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
    })

    var redIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
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
var poi_other = L.markerClusterGroup();//L.layerGroup();

var map = L.map('projectMap',{zoomControl:false,  layers: [osmColor], fullscreenControl: true}).setView([49.84, 15.17], 7);




var baseLayers = {
        "Mapa ČR": osmColor,
        "Základní mapa": cuzkZM,
        "Ortofotomapa": cuzkOrt,
        "Stínovaný reliéf 5G": cuzkEL,
    };

var overlays ={
    "Katastrální mapa":  L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 20.99, minZoom: 17, opacity: 0.5 }),
    "Katastrální území": L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom: 20.99, minZoom: 12, opacity: 0.5 })
}

L.control.layers(baseLayers,overlays).addTo(map);
L.control.scale(metric = "true").addTo(map);


L.control.zoom(
    {
        zoomInText:'+',
        zoomInTitle:'Zvětšit',
        zoomOutText:'-',
        zoomOutTitle:'Zmenšit'
    }).addTo(map)

    var buttons = [
L.easyButton({
        states: [{
            stateName: 'add-lock',
            icon: 'bi-lock',
            title: 'Zamkni pro změny',
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
            onClick: function(control) {
                global_map_can_edit=!global_map_can_edit;
                //toggleMarkerButton(true);
                map.addControl(drawControl);
                console.log("odemknout")
                control.state('add-lock');
            },
            title: 'Odemkni pro změny'
            }]
    }),

L.easyButton( 'i bi-skip-backward-fill', function(){
        //gm_correct.clearLayers();
        //editableLayers.clearLayers();
        map.setView(poi_sugest.getLayers()[0]._latlng, 18);
    },'Vrať změny')]


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
                title: 'Zruš kresbu',
                text: 'Zruš'
            },
            finish: {
                title: 'Ukonči kresbu',
                text: 'Ukonči'
            },
            undo: {
                title: 'Smaž poslední nakreslený bod',
                text: 'Smaž poslední bod'
            },
            buttons: {
                polyline: 'Nakresli linii',
                polygon: 'Nakresli polygon',
                rectangle: 'Nakresli obdélník',
                circle: 'Nakresli kruh',
                marker: 'Nakresli značku',
                circlemarker: 'Nakresli kruhovou značku'
            }
        },
        handlers: {
            circle: {
                tooltip: {
                    start: 'pro akreslení kruhu klikni a táhni.'
                },
                radius: 'Poloměr'
            },
            circlemarker: {
                tooltip: {
                    start: 'Klikni na mapu a umísti kruhovou značku.'
                }
            },
            marker: {
                tooltip: {
                    start: 'Klikni na mapu a umísti značku.'
                }
            },
            polygon: {
                tooltip: {
                    start: 'Pro nakreslení tvaru klikni.',
                    cont: 'Pro pokračování v kresbě klikni.',
                    end: 'Klikni na první bod k uzavření tvaru.'
                }
            },
            polyline: {
                error: '<strong>Chyba:</strong> hrany tvaru se nesmějí překrývat!',
                tooltip: {
                    start: 'Klikni pro začátek linie.',
                    cont: 'Klikni pro pokračování linie.',
                    end: 'Klikni poslední bod k ukončení linie.'
                }
            },
            rectangle: {
                tooltip: {
                    start: 'Pro nakreslení obdělníku klikni a táhni.'
                }
            },
            simpleshape: {
                tooltip: {
                    end: 'Uvolni kliknutí myši pro dokončení kresby.'
                }
            }
        }
    },
    edit: {
        toolbar: {
            actions: {
                save: {
                    title: 'Potvrď změny',
                    text: 'Potvrď'
                },
                cancel: {
                    title: 'Zruš editaci a zruš změny',
                    text: 'Zruš'
                },
                clearAll: {
                    title: 'Smaž vrstvu',
                    text: 'Smaž'
                }
            },
            buttons: {
                edit: 'Uprav vrstvy',
                editDisabled: 'Neexistuje vrstva k editaci',
                remove: 'Smaž vrstvy',
                removeDisabled: 'Neexistuje vrstva ke smazání'
            }
        },
        handlers: {
            edit: {
                tooltip: {
                    text: 'Vyber prvek nebo značku pro editaci.',
                    subtext: 'Klikni k návratu změn.'
                }
            },
            remove: {
                tooltip: {
                    text: 'Klikni na prvek k odstranění.'
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
            message: '<strong>Oh snap!<strong> you can\'t draw that!' // Message that will show when intersect
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
        addPointToPoiLayer(corX, corY, 'Vámi vybraná poloha záměru',la);
    } else{
        drawnItems.clearLayers();
        //gm_correct.clearLayers();
        drawnItems.addLayer(la);
    }

}
});

map.addLayer(poi_sugest);
map.addLayer(poi_other);


let points=[
        [50.2866623899293,14.83060419559479,'Moc zajimave'],
        [50.28723821959954,14.82906997203827,'1'],
        [50.286528714187945,14.829558134078981,'2'],
        [50.28633676887708,  14.825491905212404,'3'],
        [50.285658098891645,14.833227396011354,'4'],
        [50.287611819646955 ,14.832251071929933,'5']

    ]

for(i=1;i<=1000;i++){
    var x1=49+(50.4-49)*Math.random();
    var x2=13.+(18-13)*Math.random();
    points.push([x1,x2,'Random:'+i]);
}

for(i=1;i<=100;i++){
    var x1=50.28+(0.01)*Math.random();
    var x2=14.82+(0.01)*Math.random();
    points.push([x1,x2,'Random:'+i]);
}


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
        console.log(lat+'  '+ long)
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

    var polyLayers = [];
    var polygon2 = L.polygon([
        [50.2866623899293,14.83060419559479,'Moc zajimave'],
        [50.28723821959954,14.82906997203827,'1'],
        [50.286528714187945,14.829558134078981,'2'],
    ]);
    polyLayers.push(polygon2)

    for(layer of polyLayers) {
        poi_sugest.addLayer(layer);
    }
}

addPointOnLoad(50.28702571184197,14.830008745193483,"Uživatelem zadaná poloha záměru");

map.on('zoomend', function() {
    console.log(map.getZoom())
    if (map.getZoom() > 5) {
        getOtherPoi();
    }
});

map.on('click', function (e) {
        console.log("Your zoom is: "+map.getZoom())
        //var type = e.layerType;
        //console.log("Your type: "+type)
        //console.log(e)
        //console.log(map.getBounds())

});
