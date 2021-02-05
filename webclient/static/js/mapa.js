var global_map_can_edit=true;

var map = L.map('projectMap').setView([49.84, 15.17], 7);
var poi_sugest = L.layerGroup();
var poi_correct = L.layerGroup();
var poi_other = L.layerGroup();


var button_map_lock=L.easyButton({ 
    states: [{
        stateName: 'add-lock',
        icon: 'glyphicon glyphicon-stop',
        title: 'add-lock',
        onClick: function(control) {
            global_map_can_edit=!global_map_can_edit;
            control.state('remove-lock');
        }
      }, {
        icon: 'glyphicon glyphicon-play',
        stateName: 'remove-lock',
        onClick: function(control) {
            global_map_can_edit=!global_map_can_edit;
            control.state('add-lock');
        },
        title: 'remove markers'
      }]    
});
button_map_lock.addTo(map)

L.easyButton( 'glyphicon glyphicon-fast-backward', function(){
    poi_correct.clearLayers();
    map.setView(poi_sugest.getLayers()[0]._latlng, 18);
}).addTo(map)

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

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
        'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1
}).addTo(map);
map.addLayer(poi_sugest);
map.addLayer(poi_correct);
map.addLayer(poi_other);

//adding other points to layer
var getOtherPoi= ()=>{
    let points=[
        [50.2866623899293,14.83060419559479,'Moc zajimave'],
        [50.28723821959954,14.82906997203827],
        [50.286528714187945,14.829558134078981],
        [50.28633676887708,  14.825491905212404],
        [50.285658098891645,14.833227396011354],
        [50.287611819646955 ,14.832251071929933]

    ]
    points.forEach((point) => {       
        if(map.getBounds().getEast()> point[1] &&  point[1]> map.getBounds().getWest()
        &&
        map.getBounds().getSouth()< point[0] &&  point[0]< map.getBounds().getNorth()
        ){ 
            if(point.length>2){
                L.marker([point[0],point[1]]).bindPopup(point[2]).addTo(poi_other)
            } else {
                L.marker([point[0],point[1]]).addTo(poi_other)
            }

        }
    });
}

var addPointToPoiLayer = (lat, long, text) => {
    if( global_map_can_edit){
        poi_correct.clearLayers();
        L.marker([lat, long], {icon: redIcon}).bindPopup(text).addTo(poi_correct);
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
}




//addPointOnLoad(50.28702571184197,14.830008745193483,"Uživatelem zadaná poloha záměru");
/*
L.marker([50.2866623899293,14.83060419559479]).bindPopup("Moc zajimave").addTo(poi_other)
L.marker([50.28723821959954,14.82906997203827]).addTo(poi_other)
L.marker([50.286528714187945,14.829558134078981]).addTo(poi_other)*/

map.on('zoomend', function() {
    if (map.getZoom() > 10) {
        getOtherPoi();
    }
});

map.on('click', function (e) {
        console.log("Your zoom is: "+map.getZoom())
        
        let corX = e.latlng.lat;
        let corY = e.latlng.lng;
        if(corY>=12.2401111182 && corY<=18.8531441586 && corX>=48.5553052842 && corX<=51.1172677679)
        if (map.getZoom() > 15) {
            try{
                document.getElementById('id_latitude').value = corX
                document.getElementById('id_longitude').value = corY
            }catch(e){
                console.log("Error: Element id_latitude/latitude doesn exists")
            }
            //$("#detector_coordinates_x").change();
            //$("#detector_coordinates_y").change();
            addPointToPoiLayer(corX, corY, 'Vámi vybraná poloha záměru');
            //getOtherPoi();
            /*let xhr = new XMLHttpRequest();
            xhr.open('POST', '/oznameni/get-katastr-from-point');
            xhr.setRequestHeader('Content-type', 'application/json');
            if (typeof global_csrftoken !== 'undefined') {
                xhr.setRequestHeader('X-CSRFToken', global_csrftoken );
            }
            xhr.onload = function () {
                // do something to response
                console.log(JSON.parse(this.responseText).cadastre);
                document.getElementById('katastr_name').innerHTML=JSON.parse(this.responseText).cadastre;
            };
            xhr.send(JSON.stringify({ 'corY': corY,'corX': corX }))*/

        } else {
            var zoom=2;
            if(map.getZoom()<10) zoom+=2;
            else if(map.getZoom()<13) zoom+=1;

            map.setView(e.latlng, map.getZoom() + zoom);
            //console.log("Your zoom is: "+map.getZoom())
        }
});
