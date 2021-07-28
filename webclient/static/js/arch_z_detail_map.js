var global_map_can_edit=false;

var global_map_can_grab_geom_from_map=false;

var blueIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
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

var greenIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
    })

var goldIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gold.png',
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
var poi_dj = L.layerGroup();
var poi_other = L.markerClusterGroup();

//var map = L.map('djMap').setView([49.84, 15.17], 7);
//var poi = L.layerGroup();

var map = L.map('djMap',{zoomControl:false,  layers: [cuzkZM], fullscreenControl: true}).setView([49.84, 15.17], 7);




var baseLayers = {
        "Mapa ČR": osmColor,
        "Základní mapa": cuzkZM,
        "Ortofotomapa": cuzkOrt,
        "Stínovaný reliéf 5G": cuzkEL,
    };

var overlays ={
    "Katastrální mapa":  L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom: 20.99, minZoom: 17, opacity: 0.5 }),
    "Katastrální území": L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom: 20.99, minZoom: 12, opacity: 0.5 }),
    "Piany": poi_other
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
                    icon: 'glyphicon-lock',
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
                    icon: 'glyphicon-pencil',
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

        L.easyButton( 'bi bi-skip-backward-fill', function(){
                //gm_correct.clearLayers();
                //editableLayers.clearLayers();
                map.setView(poi_sugest.getLayers()[0]._latlng, 18);
                edit_buttons.disable();
            },'Vrať změny')]


var edit_buttons=L.easyBar(buttons)
map.addControl(edit_buttons)

var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

L.EditToolbar.Delete.include({
    removeAllLayers: false
});
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
                if( global_map_can_edit){
                    L.marker([corX, corY], {icon: redIcon}).bindPopup('Navržený pian').addTo(drawnItems);

                }
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
map.addLayer(poi_dj);

function geomToText(){
    // LINESTRING(-71.160281 42.258729,-71.160837
    // POLYGON((-71.1776585052917 42.3902909739571,-71.177682
    // POINT(-71.064544 42.28787)');
    var text="";
    drawnItems.eachLayer(function(layer) {
         if (layer instanceof L.Marker) {
            //addLogText('im an instance of L marker');
            //console.log(layer)
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



var addPointToPoiLayerWithForce = (lat, long, text,lai) => {
        L.marker([lat, long], {icon: redIcon,zIndexOffset:2000}).bindPopup(text).addTo(drawnItems);
}
var addPointToPoiLayerWithForceG =(st_text,layer,text,overview=false) => {
    let coor=[]
    let myIco={icon: blueIcon};

    function mouseOverGeometry(geom){
        function getContent(e){
            let content="";
            try{
                content = e.target.getPopup().getContent();
            }catch(ee){
                content = e.target.getTooltip().getContent();
            }
            return content;
        }

        geom.on('click', function (e) {
            if(global_map_can_grab_geom_from_map!==false){
                $.ajax({
                    type: "GET",
                    url:"/pian/list-pians/?q="+getContent(e),
                    dataType: 'json',
                    success: function(data){
                      if(data.results.length>0){
                      $('#id_'+global_map_can_grab_geom_from_map+'-pian').select2("trigger", "select",{data:data.results[0]})
                      }
                      global_map_can_grab_geom_from_map=false;

                    },
                    error: ()=>{
                        global_map_can_grab_geom_from_map=false;
                    }
                  })
            }
        })

        geom.on('mouseover', function() {

            if (geom instanceof L.Marker){
                this.options.iconOld=this.options.icon;
                this.setIcon(goldIcon);
            } else {
                this.options.iconOld=this.options.color;
                this.setStyle({color: 'red'});
            }
        });

        geom.on('mouseout', function() {
            //
            if (geom instanceof L.Marker){
            this.setIcon(this.options.iconOld);
            } else {
                this.setStyle({color:this.options.iconOld});
            }
            delete this.options.iconOld;
        })
    }

    if (layer===poi_dj){
        //console.log(text+" orange "+st_text)
        myIco={icon: greenIcon,zIndexOffset:1000};
    } else if(layer==gm_correct){
        myIco={icon: redIcon};
    }

    if(st_text.includes("POLYGON")){
        st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
            coor.push([i.split(" ")[1],i.split(" ")[0]])
        })
        mouseOverGeometry(L.polygon(coor).bindTooltip(text).addTo(layer));
    }else if(st_text.includes("LINESTRING")){
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            coor.push([i.split(" ")[1],i.split(" ")[0]])
        })
        mouseOverGeometry(L.polyline(coor).bindTooltip(text).addTo(layer));
    } else if(st_text.includes("POINT")){
        let i=st_text.split("(")[1].split(")")[0];
        coor.push([i.split(" ")[1],i.split(" ")[0]])
        if(layer===poi_other){
            mouseOverGeometry(L.marker([i.split(" ")[1], i.split(" ")[0]], myIco).bindTooltip(text).addTo(layer));
        }

    }
    if(overview && coor.length>0 && layer!==poi_other){
        x0=0.0;
        x1=0.0
        c0=0
        //console.log(coor)
        for(const i of coor){
            x0=x0+parseFloat(i[0])
            x1=x1+parseFloat(i[1])
            c0=c0+1
        }
        L.marker([x0/c0,x1/c0], myIco).bindPopup(text).addTo(layer);

    }
}

function addLogText(text) {
    //addLogText(text);
    //geomToText();
    console.log(text)
}

function addGeometry(text) {
    let geom=document.getElementById("id_geom");
    geom.value=text;
    if(poi_sugest.getLayers().size){
        edit_buttons.enable();
    }
}
