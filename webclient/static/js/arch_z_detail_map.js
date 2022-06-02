var global_map_can_edit=false;

var global_map_can_grab_geom_from_map=false;
var global_map_element="id_geom";
var global_map_element_sjtsk="id_geom_sjtsk";
console.log("zmena def.geom :"+global_map_element)


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
var heatPoints = [];
var heatLayer  = L.heatLayer(heatPoints);

var global_clusters=false;
var global_heat=false;

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
            icon: pinIconRedPoint
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
    //console.log(document.getElementById(global_map_element).value)
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
    addWGS84Geometry()
    addSJTSKGeometry()
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
        //console.log(e)

        if (type === 'marker'){
            drawnItems.clearLayers();

            let corX = e.layer._latlng.lat;
            let corY = e.layer._latlng.lng;
                if( global_map_can_edit){
                    L.marker([corX, corY], {icon: pinIconRedPoint}).bindPopup('Navržený pian').addTo(drawnItems);

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
    var jtsk_text=""
    var jtsk_coor=[]
    let coordinates = [];
    drawnItems.eachLayer(function(layer) {
         if (layer instanceof L.Marker) {
            //addLogText('im an instance of L marker');
            //console.log(layer)
            let latlngs=layer.getLatLng()
            text="POINT("+latlngs.lng+" "+latlngs.lat+")"
            jtsk_coor = convertToJTSK(latlngs.lat, latlngs.lng);
            jtsk_text="POINT("+jtsk_coor[0]+" "+jtsk_coor[1]+")"
            //coordinates.push([latlngs.lng, latlngs.lat])
        }
        else if (layer instanceof L.Polygon) {
            //addLogText('im an instance of L polygon');
            text="POLYGON(("
            jtsk_text="POLYGON(("
            let latlngs=layer.getLatLngs()
            for (var i = 0; i < latlngs.length; i++) {
                for(var j=0; j< latlngs[i].length;j++){
                    coordinates.push([latlngs[i][j].lng, latlngs[i][j].lat])
                    text +=( latlngs[i][j].lng+" "+latlngs[i][j].lat) + ", ";
                    jtsk_coor = convertToJTSK(latlngs[i][j].lat, latlngs[i][j].lng);
                    jtsk_text +=( jtsk_coor[0]+" "+jtsk_coor[1]) + ", ";
                }
            }
            // Musi koncit na zacatek
            text += coordinates[0][0] + " " + coordinates[0][1]
            text +="))"
            jtsk_coor = convertToJTSK(coordinates[0][1], coordinates[0][0]);
            jtsk_text += jtsk_coor[0] + " " + jtsk_coor[1]
            jtsk_text +="))"
        }
        else if (layer instanceof L.Polyline) {
            //addLogText('im an instance of L polyline');
            text="LINESTRING("
            jtsk_text="LINESTRING("
            let it=0;
            coordinates=layer.getLatLngs()
            for (let i in coordinates){
                if(it>0) {text +=","; jtsk_text +=",";}

                it++;
                text +=( coordinates[i].lng+" "+coordinates[i].lat);
                jtsk_coor = convertToJTSK(coordinates[i].lat, coordinates[i].lng);
                jtsk_text +=( jtsk_coor[0]+" "+jtsk_coor[1]);
            }
            text +=")"
            jtsk_text +=")"
        }
        addWGS84Geometry(amcr_static_geom_precision_wgs84(text),global_map_can_edit);
        addSJTSKGeometry(amcr_static_geom_precision_jtsk(jtsk_text),global_map_can_edit);
    });



}

var mouseOverGeometry =(geom)=>{
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
                url:"/pian/seznam-pian/?q="+getContent(e),
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
            if(this.options.changeIcon){
                this.setIcon(pinIconYellow);
            }else{
                this.setIcon(pinIconYellowPoint);
            }
        } else {
            this.options.iconOld=this.options.color;
            this.setStyle({color: 'gold'});
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

var addPointToPoiLayerWithForce = (geom, layer,text,st_text) => {
    //console.log(text)
    //console.log(geom)
    let coor=[]
    if(st_text.includes("POLYGON") || st_text.includes("LINESTRING")){
        mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84(geom), {icon: pinIconRed,zIndexOffset:2000,changeIcon:true}).bindPopup(text).addTo(layer));
        if(st_text.includes("POLYGON")){
            st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
                coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1],i.split(" ")[0]]));
            })
            mouseOverGeometry(L.polygon(coor,{color:'red'}).bindTooltip(text,{sticky: true }).addTo(layer));
        }else if(st_text.includes("LINESTRING")){
            st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
                coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1],i.split(" ")[0]]))
            })
            mouseOverGeometry(L.polyline(coor,{color:'red'}).bindTooltip(text,{sticky: true }).addTo(layer));
        }
    } else{
        mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84(geom), {icon: pinIconRedPoint,zIndexOffset:2000}).bindPopup(text).addTo(layer));
    }

}
var addPointToPoiLayerWithForceG =(st_text,layer,text,overview=false) => {
    let coor=[]
    let myIco={icon: pinIconBluePoint};
    let myIco2={icon: pinIconBlue};
    let myColor= {color:"rgb(51, 153, 255)"};



    if (layer===poi_dj){
        //console.log(text+" orange "+st_text)
        myIco={icon: pinIconGreenPoint,zIndexOffset:1000};
        myIco2={icon: pinIconGreen,zIndexOffset:1000,changeIcon:true};
        myColor={color:'green',zIndexOffset:1000,};
    } /*else if(layer==gm_correct){
        myIco={icon: pinIconRedPoint};
        myIco2={icon: pinIconRed};
        myColor='red';
    }*/

    if(st_text.includes("POLYGON")){
        st_text.split("((")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1],i.split(" ")[0]]))
        })
        mouseOverGeometry(L.polygon(coor,myColor).bindTooltip(text,{sticky: true }).addTo(layer));
    }else if(st_text.includes("LINESTRING")){
        st_text.split("(")[1].split(")")[0].split(",").forEach(i => {
            coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1],i.split(" ")[0]]))
        })
        mouseOverGeometry(L.polyline(coor,myColor).bindTooltip(text,{sticky: true }).addTo(layer));
    } else if(st_text.includes("POINT")){
        let i=st_text.split("(")[1].split(")")[0];
        coor.push(amcr_static_coordinate_precision_wgs84([i.split(" ")[1],i.split(" ")[0]]))
        if(layer===poi_other){
            mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84([i.split(" ")[1], i.split(" ")[0]]), myIco).bindTooltip(text).addTo(layer));
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
        if(st_text.includes("POLYGON") || st_text.includes("LINESTRING")){
            mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84([x0/c0,x1/c0]), myIco2).bindTooltip(text).addTo(layer));
        }else{
            mouseOverGeometry(L.marker(amcr_static_coordinate_precision_wgs84([x0/c0,x1/c0]), myIco).bindTooltip(text).addTo(layer));
        }

    }
    //heatPoints.push()
    drawnItems.bringToFront();
}

function addLogText(text) {
    //addLogText(text);
    //geomToText();
    //console.log(text)
}

function addWGS84Geometry(text) {
    console.log("add-geometry: "+global_map_element)
    let geom=document.getElementById(global_map_element);
    if(geom){
        console.log("+w")
        geom.value=text;
    }
    if(poi_sugest.getLayers().size){
        edit_buttons.enable();
    }
}

function addSJTSKGeometry(text) {
    console.log("add-geometry: "+global_map_element_sjtsk)
    let geom_sjtsk=document.getElementById(global_map_element_sjtsk);
    if(geom_sjtsk){
        geom_sjtsk.value=text;
        console.log("+j")
    }
    if(poi_sugest.getLayers().size){
        edit_buttons.enable();
    }
}

function clearUnfinishedEditGeometry(){
    global_map_element="id_geom";
    global_map_element_sjtsk="id_geom_sjtsk";
    console.log("zmena def.geom :"+global_map_element)
    global_map_can_grab_geom_from_map=false;
    map_show_edit(false, false)
    drawnItems.clearLayers();
    drawnItemsBuffer.eachLayer(function (layer){
        layer.addTo(poi_dj)
    })
}

function loadGeomToEdit(ident_cely){
    console.log("load")
    drawnItems.clearLayers();
    drawnItemsBuffer.clearLayers();
    let drawnItemsCount=0;
    let layerColor="green";
    let PolylineColor= '#97009c';
    let PolygonColor= '#662d91' ;
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
                        //UNDO-layer-start
                        L.marker(amcr_static_coordinate_precision_wgs84([latlngs.lat,latlngs.lng]),{icon: pinIconBluePoint}).bindPopup(content).addTo(drawnItemsBuffer);
                        //UNDO-layer-end
                    } else{
                        layer.remove();
                    }
                } else if (layer instanceof L.Polygon){
                    if(drawnItemsCount>1){
                        drawnItems.clearLayers();
                    }
                    layerColor=layer.options.color;
                    layer.setStyle({color: PolygonColor});
                    layer.addTo(drawnItems);
                    //UNDO-layer-start
                    let latlngs=layer.getLatLngs()
                    let coordinates=[];
                    for (var i = 0; i < latlngs.length; i++) {
                        for(var j=0; j< latlngs[i].length;j++){
                            coordinates.push(amcr_static_coordinate_precision_wgs84([latlngs[i][j].lat, latlngs[i][j].lng]))
                        }
                    }
                    L.polygon(coordinates,{color:layerColor}).bindTooltip(content,{sticky:true}).addTo(drawnItemsBuffer);
                    //UNDO-layer-end
                } else if (layer instanceof L.Polyline) {
                    if(drawnItemsCount>1){
                        drawnItems.clearLayers();
                    }
                    layerColor=layer.options.color;
                    layer.setStyle({color: PolylineColor});
                    layer.addTo(drawnItems);
                    //UNDO-layer-start
                    let latlngs=layer.getLatLngs()
                    let coordinates=[];
                    for (let i in latlngs){
                        coordinates.push(amcr_static_coordinate_precision_wgs84([latlngs[i].lat,latlngs[i].lng]));
                    }
                    L.polyline(coordinates,{color:layerColor}).bindTooltip(content,{sticky:true}).addTo(drawnItemsBuffer);
                    //UNDO-layer-end
                }
            }
        }
    })
    if(drawnItemsCount){

        global_map_element="id_"+ident_cely+"-geom"
        global_map_element_sjtsk="id_"+ident_cely+"-geom_sjtsk"
        console.log("zmena def.geom :"+global_map_element)
        geomToText();
        drawControl._toolbars.edit._modes.edit.handler.enable();
    } else{
        console.log("zmena def.geom :chyba")
    }

}

//switchMap ();
var boundsLock=0;

map.on('zoomend', function() {
    console.log("zoomed")
    switchMap(true)
});



map.on('moveend', function() {
    console.log("moved");
    switchMap(false)
    //var bounds = map.getBounds();
    //var northWest = bounds.getNorthWest(),
    //    southEast = bounds.getSouthEast();
   // console.log("Change: "+northWest+"  "+southEast)
   //var geomCount=0;
   //if(map.getZoom()>=15){
});

heatPoints = heatPoints.map(function (p) {
    var bounds = map.getBounds();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();
    if(northWest.lat>=p[0] && southEast.lat<=p[0]){
                if(northWest.lng<=p[1] && southEast.lng>=p[1]){
                    return [p[0], p[1]];
                }
            }
});



switchMap = function(overview=false){
    var bounds = map.getBounds();
    let zoom=map.getZoom();
    var northWest = bounds.getNorthWest(),
        southEast = bounds.getSouthEast();
    if(!global_map_can_edit){
    if(overview || bounds.northWest != boundsLock.northWest || !boundsLock.northWest){
        console.log("Change: "+northWest+"  "+southEast+" "+zoom);
        boundsLock=bounds;
        let xhr = new XMLHttpRequest();
        xhr.open('POST', '/arch-z/akce-get-piany');
        xhr.setRequestHeader('Content-type', 'application/json');
        if (typeof global_csrftoken !== 'undefined') {
            xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
        }
        xhr.send(JSON.stringify(
            {
                'northWest': northWest,
                'southEast': southEast,
                'zoom': zoom,
                'dj_ident_cely':global_map_projekt_ident,
            }));
        xhr.onload = function () {
            //console.log(JSON.parse(this.responseText))
            poi_other.clearLayers();
            poi_dj.clearLayers();
            heatPoints=[]
            map.removeLayer(heatLayer);
            //gm_correct.clearLayers();
                let resAl=JSON.parse(this.responseText).algorithm
                if(resAl == "detail"){
                    let resPoints=JSON.parse(this.responseText).points
                    //let dj_head=form_id.replace("detail_dj_form_", "")
                    resPoints.forEach((i)=>{
                    if(i.dj != null){
                        //console.log(i.geom+" "+poi_dj+" "+i.ident_cely)
                        addPointToPoiLayerWithForceG(i.geom,poi_dj,i.ident_cely,true)
                    }
                    else {
                        addPointToPoiLayerWithForceG(i.geom,poi_other,i.ident_cely,true)
                    }
                    })
                }else{
                    console.log("heat");
                    let resHeat=JSON.parse(this.responseText).heat
                    resHeat.forEach((i)=>{

                        geom=i.geom.split("(")[1].split(")")[0].split(" ");
                        for(let j=0;j<i.pocet;j++){
                            heatPoints.push([geom[1],geom[0]])//chyba je to geome
                        }
                    })
                    heatLayer=L.heatLayer(heatPoints);
                    map.addLayer(heatLayer);
                    poi_other.clearLayers();
                    poi_dj.clearLayers();
                }
                console.log("loaded")
        }
        }
    }
}
