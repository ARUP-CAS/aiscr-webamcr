var global_map_can_edit=false;

var global_map_can_grab_geom_from_map=false;
var global_map_element="id_geom";

var blueIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [18, 29],
    iconAnchor: [9, 29],
    popupAnchor: [1, -24],
    shadowSize: [29, 29]
    })

var redIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [18, 29],
    iconAnchor: [9, 29],
    popupAnchor: [1, -24],
    shadowSize: [29, 29]
    })

var greenIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [18, 29],
    iconAnchor: [9, 29],
    popupAnchor: [1, -24],
    shadowSize: [29, 29]
    })

var goldIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gold.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [18, 29],
    iconAnchor: [9, 29],
    popupAnchor: [1, -24],
    shadowSize: [29, 29]
    })

var osmColor = L.tileLayer('http://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM map', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkWMS = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'KN', maxZoom:25, maxNativeZoom: 20, minZoom: 17, opacity: 0.5 }),
    cuzkWMS2 = L.tileLayer.wms('http://services.cuzk.cz/wms/wms.asp?', { layers: 'prehledka_kat_uz', maxZoom:25, maxNativeZoom: 20, minZoom: 12, opacity: 0.5 }),
    cuzkOrt = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/ortofoto_wm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'ortofoto_wm', maxZoom:25, maxNativeZoom: 19, minZoom: 6 }),
    cuzkEL = L.tileLayer.wms('http://ags.cuzk.cz/arcgis2/services/dmr5g/ImageServer/WMSServer?', { layers: 'dmr5g:GrayscaleHillshade', maxZoom: 25, maxNativeZoom: 20, minZoom: 6 }),
    cuzkZM = L.tileLayer('http://ags.cuzk.cz/arcgis/rest/services/zmwm/MapServer/tile/{z}/{y}/{x}?blankTile=false', { layers: 'zmwm', maxZoom: 25,maxNativeZoom:19, minZoom: 6 });

var poi_sugest = L.layerGroup();
var gm_correct = L.layerGroup();
var poi_dj = L.layerGroup();
var poi_other = L.markerClusterGroup({disableClusteringAtZoom:20});

var map = L.map('djMap', {
    layers: [cuzkZM, poi_other],
    zoomControl: false,
    contextmenu: true,
    contextmenuWidth: 140,
    contextmenuItems: []

}).setView([49.84, 15.17], 7);

map.addLayer(poi_sugest);
map.addLayer(poi_other);
map.addLayer(poi_dj);

var baseLayers = {
    "ČÚZK - Základní mapy ČR": cuzkZM,
    "ČÚZK - Ortofotomapa": cuzkOrt,
    "ČÚZK - Stínovaný reliéf 5G": cuzkEL,
    "OpenStreetMap": osmColor,
};

var overlays = {
    "ČÚZK - Katastrální mapa": cuzkWMS,
    "ČÚZK - Katastrální území": cuzkWMS2,
    "AMČR Piany": poi_other
};

L.control.layers(baseLayers,overlays).addTo(map);
L.control.scale(metric = "true").addTo(map);

map.addControl(new L.Control.Fullscreen({
    title: {
        'false': 'Celá obrazovka',
        'true': 'Opustit celou obrazovku'
    }
}));
map.addControl(new L.control.zoom(
    {
        zoomInText:'+',
        zoomInTitle:'Přiblížit',
        zoomOutText:'-',
        zoomOutTitle:'Oddálit'
    }))

var buttons = [
    L.easyButton( 'bi bi-skip-backward-fill', function(){
            map.setView(poi_sugest.getLayers()[0]._latlng, 18);
            edit_buttons.disable();
        },'Výchozí stav')]

var edit_buttons=L.easyBar(buttons)
map.addControl(edit_buttons)

var drawnItems = new L.FeatureGroup();
var drawnItemsBuffer = new L.FeatureGroup();
map.addLayer(drawnItems);

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
                title: 'Storno',
                text: 'Storno'
            },
            finish: {
                title: 'Dokončit',
                text: 'Dokončit'
            },
            undo: {
                title: 'Krok zpět',
                text: 'Krok zpět'
            },
            buttons: {
                polyline: 'Přidat linii',
                polygon: 'Přidat polygon',
                rectangle: 'Přidat obdélník',
                circle: 'Přidat kruh',
                marker: 'Přidat bod',
                circlemarker: 'Přidat kruhový bod'
            }
        },
        handlers: {
            circle: {
                tooltip: {
                    start: 'Pro nakreslení kruhu klikni a táhni.'
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
                    title: 'Dokončit',
                    text: 'Dokončit'
                },
                cancel: {
                    title: 'Storno',
                    text: 'Storno'
                },
                clearAll: {
                    title: 'Smazat',
                    text: 'Smazat'
                }
            },
            buttons: {
                edit: 'Uprav vymezení',
                editDisabled: 'Neexistuje vrstva k editaci',
                remove: 'Smazat',
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

var measureControl=new L.control.measure({title:"Měřit vzdálenost"});
map.addControl(measureControl);

map.addControl(new L.control.coordinates({
    position:"bottomright",
    useDMS:true,
    labelTemplateLat:"N {y}",
    labelTemplateLng:"E {x}",
    useLatLngOrder:true,
    centerUserCoordinates: true,
    markerType: null
}));

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

map.on('contextmenu',(e) => {

    var features = [];
    map.contextmenu.removeAllItems();
    map.contextmenu.addItem({text:'Přenes do popředí:',disabled:true})
    map.eachLayer(function (layer) {
       if (layer instanceof L.Polyline || layer instanceof L.Polygon ){
         if(layer.getBounds().contains(e.latlng)) {
          features.push(layer.getTooltip().getContent());
           //console.log(layer.getTooltip().getContent());
           map.contextmenu.addItem({
           text: layer.getTooltip().getContent(),
           callback: function (){layer.bringToFront() }
           })
         }
       }
       // do something with the layer
     });
     if(features.length == 0){
       map.contextmenu.hide();
     } else {
      map.contextmenu.showAt(e.latlng, features)
     }

   //  console.log(markersLayer.length())
});

function disableSavePianButton(){
    console.log("disableSavePianButton")
    console.log(document.getElementById(global_map_element).value)
    if(document.getElementById(global_map_element).value==='undefined'){
        document.getElementById("editPianButton").disabled = true;
        console.log("disableSavePianButton:disa")
    } else {
        document.getElementById("editPianButton").disabled = false;
        console.log("disableSavePianButton:enable")
    }
}

map.on('draw:edited', function (e) {
    addLogText("edited")
    geomToText();
});
map.on('draw:deleted', function(e) {
    addLogText("deleted")
    addGeometry()
    disableSavePianButton();
    //console.log(document.getElementById(global_map_element));
    //console.log(document.getElementById("editPianButton"))//editPianButton

})

map.on('draw:drawstart',function(e){
    if(measureControl._measuring){
        measureControl._stopMeasuring()
    }
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
        disableSavePianButton();

    }
});



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
        addGeometry(text,global_map_can_edit);
    });



}



var addPointToPoiLayerWithForce = (geom, layer,text) => {
        L.marker(geom, {icon: redIcon,zIndexOffset:2000}).bindPopup(text).addTo(layer);
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
            if(measureControl._measuring){
                measureControl._stopMeasuring()
            }
            if(global_map_can_grab_geom_from_map!==false){
                $.ajax({
                    type: "GET",
                    url:"/pian/list-pians/?q="+getContent(e),
                    dataType: 'json',
                    success: function(data){
                      if(data.results.length>0){
                      $('#id_'+global_map_can_grab_geom_from_map+'-pian').select2("trigger", "select",{data:data.results[0]})
                      }
                      //global_map_can_grab_geom_from_map=false;

                    },
                    error: ()=>{
                       // global_map_can_grab_geom_from_map=false;
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
        mouseOverGeometry(L.polygon(coor).bindTooltip(text,{sticky: true }).addTo(layer));
    }else if(st_text.includes("LINESTRING")){
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            coor.push([i.split(" ")[1],i.split(" ")[0]])
        })
        mouseOverGeometry(L.polyline(coor).bindTooltip(text,{sticky: true }).addTo(layer));
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
    console.log("add-geometry: "+global_map_element)
    let geom=document.getElementById(global_map_element);
    if(geom){
        geom.value=text;
    }
    if(poi_sugest.getLayers().size){
        edit_buttons.enable();
    }
}

function clearUnfinishedEditGeometry(){
    global_map_element="id_geom";
    global_map_can_grab_geom_from_map=false;
    map_show_edit(false, false)
    drawnItems.clearLayers();
    drawnItemsBuffer.eachLayer(function (layer){
        layer.addTo(poi_dj)
    })
}

function loadGeomToEdit(ident_cely){
    drawnItems.clearLayers();
    drawnItemsBuffer.clearLayers();
    let drawnItemsCount=0;
    map.eachLayer(function (layer) {
        if (layer instanceof L.Polyline || layer instanceof L.Polygon || layer instanceof L.Marker ){
            let content="";
            try{
                content = layer.getPopup().getContent();
            }catch(ee){
                try{
                    content = layer.getTooltip().getContent();
                } catch(eee){
                   // console.log(layer)
                }
            }
            if(content==ident_cely){
                drawnItemsCount=drawnItemsCount+1;
                if(layer instanceof L.Marker){
                    let latlngs=layer.getLatLng()
                    if(drawnItemsCount==1){
                        layer.addTo(drawnItems);
                        L.marker([latlngs.lat,latlngs.lng],{icon: blueIcon}).bindPopup(content).addTo(drawnItemsBuffer);
                        //drawnItemsBuffer.push({type:"Marker", coor:layer.getLatLng(), content:content});
                    } else{
                       // L.marker([latlngs.lat,latlngs.lng]).bindPopup(content).addTo(drawnItemsBuffer);
                        layer.remove();
                    }
                } else if (layer instanceof L.Polygon){
                    if(drawnItemsCount>1){
                        drawnItems.clearLayers();
                    }
                    layer.addTo(drawnItems);
                    let latlngs=layer.getLatLngs()
                    let coordinates=[];
                    for (var i = 0; i < latlngs.length; i++) {
                        for(var j=0; j< latlngs[i].length;j++){
                            coordinates.push([latlngs[i][j].lat, latlngs[i][j].lng])
                        }
                    }
                    L.polygon(coordinates).bindTooltip(content,{sticky:true}).addTo(drawnItemsBuffer);
                    //drawnItemsBuffer.push({type:"Polygon", coor:layer.getLatLngs(), content:content});
                } else if (layer instanceof L.Polyline) {
                    if(drawnItemsCount>1){
                        drawnItems.clearLayers();
                    }
                    layer.addTo(drawnItems);
                    let latlngs=layer.getLatLngs()
                    let coordinates=[];
                    for (let i in latlngs){
                        coordinates.push([latlngs[i].lat,latlngs[i].lng]);
                    }
                    L.polyline(coordinates).bindTooltip(content,{sticky:true}).addTo(drawnItemsBuffer);
                    //drawnItemsBuffer.push({type:"Polyline", coor:layer.getLatLngs(), content:content});
                }
            }
        }
    })
    if(drawnItemsCount){
        global_map_element="id_"+ident_cely+"-geom"
        geomToText();
        drawControl._toolbars.edit._modes.edit.handler.enable();
    }

}
