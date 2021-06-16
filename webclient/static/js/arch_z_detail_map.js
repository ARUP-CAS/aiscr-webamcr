var global_map_can_edit=false;

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
var poi_other = L.layerGroup(); //L.markerClusterGroup();

//var map = L.map('djMap').setView([49.84, 15.17], 7);
//var poi = L.layerGroup();

var map = L.map('djMap',{zoomControl:false,  layers: [osmColor], fullscreenControl: true}).setView([49.84, 15.17], 7);




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
        /*L.easyButton({
                states: [{
                    stateName: 'add-lock',
                    icon: 'glyphicon glyphicon-lock',
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
                    icon: 'glyphicon glyphicon-pencil',
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
            }),*/

        L.easyButton( '<<', function(){
                //gm_correct.clearLayers();
                //editableLayers.clearLayers();
                map.setView(poi_sugest.getLayers()[0]._latlng, 18);
                edit_buttons.disable();
            },'Vrať změny')]


var edit_buttons=L.easyBar(buttons)
map.addControl(edit_buttons)

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

function map_show_edit(show, show_go_back){
    global_map_can_edit=show;
    if(!show){
        map.removeControl(edit_buttons)
        map.removeControl(drawControl)

        //edit_buttons.disable();

    } else if (show){
        if(show_go_back){
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

map.on('draw:edited', function (e) {

    var layers = e.layers;
    var countOfEditedLayers = 0;
    layers.eachLayer(function(layer) {
        countOfEditedLayers++;
    });
    console.log("Edited " + countOfEditedLayers + " layers");
    addLogText("edit")
    geomToText();
});
map.on('draw:deleted', function(e) {
    addLogText("deleted")
    addGeometry("")
})

map.on('draw:created', function(e) {

if(global_map_can_edit){
    var type = e.layerType;
    var la = e.layer;
    console.log(e)


    if (type === 'marker'){
        drawnItems.clearLayers();

        let corX = e.layer._latlng.lat;
        let corY = e.layer._latlng.lng;
        addPointToPoiLayer(corX, corY, 'Navržený PIAN',la);
    } else{
        drawnItems.clearLayers();
        //gm_correct.clearLayers();
        drawnItems.addLayer(la);
    }
    addLogText("created")
    geomToText();

}
});

map.addLayer(poi_sugest);
map.addLayer(poi_other);

function geomToText(){
    // LINESTRING(-71.160281 42.258729,-71.160837
    // POLYGON((-71.1776585052917 42.3902909739571,-71.177682
    // POINT(-71.064544 42.28787)');
    var text="";
    drawnItems.eachLayer(function(layer) {
         if (layer instanceof L.Marker) {
            //addLogText('im an instance of L marker');
            console.log(layer)
            let latlngs=layer.getLatLng()
            text="POINT("+latlngs.lng+" "+latlngs.lat+")"
        }
        else if (layer instanceof L.Polygon) {
            //addLogText('im an instance of L polygon');
            text="POLYGON(("
            let coordinates = [];
            let latlngs=layer.getLatLngs()
            for (var i = 0; i < latlngs.length; i++) {
                for(var j=0; j< latlngs[i].length;j++){
                    coordinates.push([latlngs[i][j].lat, latlngs[i][j].lng])
                    text +=( latlngs[i][j].lng+" "+latlngs[i][j].lat) + ", ";
                }
            }
            // Musi koncit na zacatek
            text += coordinates[0][1] + " " + coordinates[0][0]
            text +="))"
        }
        else if (layer instanceof L.Polyline) {
            //addLogText('im an instance of L polyline');
            text="LINESTRING("
            let it=0;
            let coordinates=layer.getLatLngs()
            for (let i in coordinates){
                if(it>0) text +=","

                it++;
                text +=( coordinates[i].lng+" "+coordinates[i].lat);
            }
            text +=")"
        }
        addGeometry(text);
    });



}

var addPointToPoiLayer = (lat, long, text,lai) => {
    if( global_map_can_edit){
        L.marker([lat, long], {icon: redIcon}).bindPopup(text).addTo(drawnItems);

    }
}

var addPointToPoiLayerWithForce = (lat, long, text,lai) => {
        L.marker([lat, long], {icon: redIcon,zIndexOffset:1000}).bindPopup(text).addTo(drawnItems);
}
var addPointToPoiLayerWithForceG =(st_text,layer,text) => {
    let coor=[]
    if(st_text.includes("POLYGON")){
        st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
            console.log(i)
            coor.push([i.split(" ")[1],i.split(" ")[0]])
        })
        L.polygon(coor).addTo(drawnItems);
        console.log(coor)
    }else if(st_text.includes("LINESTRING")){
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            console.log(i)
            coor.push([i.split(" ")[1],i.split(" ")[0]])
        })
        L.polyline(coor).addTo(layer);
        console.log(coor)
    } else if(st_text.includes("POINT")){
        let i=st_text.split("(")[1].split(")")[0];
        L.marker([i.split(" ")[1], i.split(" ")[0]], {icon: greenIcon}).bindPopup(text).addTo(layer);

    }
}

var addPianFromKadastre =(st_text,text) => {
    let coor=[]
    if(st_text.includes("POLYGON")){
        st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
                coor.push([i.split(" ")[0],i.split(" ")[1]])
        })
        L.polygon(coor).addTo(poi_other);
        console.log(coor)
    }else if(st_text.includes("LINESTRING")){
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            coor.push([i.split(" ")[0],i.split(" ")[1]])
        })
        L.polyline(coor).addTo(poi_other);
        console.log(coor)
    } else if(st_text.includes("POINT")){
        let i=st_text.split("(")[1].split(")")[0];
        L.marker([i.split(" ")[0], i.split(" ")[1]], {icon: greenIcon}).bindPopup(text).addTo(poi_other);

    }
}

function addLogText(text) {
    //addLogText(text);
    //geomToText();
    console.log(text)
}

function addGeometry(text) {
    console.log(text)
    let geom=document.getElementById("id_geom");
    geom.value=text;
    if(poi_sugest.getLayers().size){
        edit_buttons.enable();
    }
    //addLogText(text);
    //geomToText();
    //console.log(text);
}
