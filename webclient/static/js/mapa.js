var global_map_can_edit=true;

var map = L.map('projectMap').setView([49.84, 15.17], 7);
var poi_sugest = L.layerGroup();
var poi_correct = L.layerGroup();
var poi_other = L.layerGroup();


var button_map_lock=L.easyButton({
    states: [{
        stateName: 'add-lock',
        icon: 'bi bi-stop-fill',
        title: 'add-lock',
        onClick: function(control) {
            global_map_can_edit=!global_map_can_edit;
            control.state('remove-lock');
        }
      }, {
        icon: 'bi bi-play-fill',
        stateName: 'remove-lock',
        onClick: function(control) {
            global_map_can_edit=!global_map_can_edit;
            control.state('add-lock');
        },
        title: 'remove markers'
      }]
});
button_map_lock.addTo(map)

L.easyButton( 'bi bi-skip-backward-fill', function(){
    poi_correct.clearLayers();
    let ll=poi_sugest.getLayers()[0]._latlng;
    map.setView(ll, 18);
    try{
        document.getElementById('id_latitude').value = ll.lat;
        document.getElementById('id_longitude').value = ll.lng;
    }catch(e){
        console.log("Error: Element id_latitude/latitude doesn exists")
    }
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

    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/projekt/get-points-arround-point');
    xhr.setRequestHeader('Content-type', 'application/json');
    if (typeof global_csrftoken !== 'undefined') {
        xhr.setRequestHeader('X-CSRFToken', global_csrftoken );
    }
    xhr.onload = function () {
        // do something to response
        poi_other.clearLayers();
        console.log(poi_sugest.getLayers()[0]._latlng)
        JSON.parse(this.responseText).points.forEach((point) => {
            if(poi_sugest.getLayers()[0]._latlng.lat!=point.lat && poi_sugest.getLayers()[0]._latlng.lng !=point.lng)
            L.marker([point.lat,point.lng]).bindPopup(point.ident_cely).addTo(poi_other)
        })
    };
    xhr.send(JSON.stringify({ 'NorthWest': map.getBounds().getNorthWest(),'SouthEast': map.getBounds().getSouthEast() }))
}

const addPointToPoiLayer = (lat, long, text) => {
    if (global_map_can_edit) {
        poi_correct.clearLayers();
        L.marker([lat, long], {icon: redIcon}).bindPopup(text).addTo(poi_correct);
        const getUrl = window.location;
        const select = $("#id_hlavni_katastr");
        if (select) {
            fetch(getUrl.protocol + "//" + getUrl.host + `/heslar/zjisti-katastr-souradnic/?long=${long}&lat=${lat}`)
                .then(response => response.json())
                .then(response => {
                    select.val(response['id']);
                })
        }
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
    //getOtherPoi();
}

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
