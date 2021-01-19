var map = L.map('projectMap').setView([49.84, 15.17], 7);
var poi = L.layerGroup();

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
        'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1
}).addTo(map);
map.addLayer(poi);

var addPointToPoiLayer = (lat, long, text) => {
        L.marker([lat, long]).bindPopup(text).addTo(poi);
}

map.on('click', function (e) {
    poi.clearLayers();
	let corX = e.latlng.lat;
	let corY = e.latlng.lng;
	if (map.getZoom() > 15) {
		document.getElementById('id_latitude').value = corX
		document.getElementById('id_longitude').value = corY
        //$("#detector_coordinates_x").change();
        //$("#detector_coordinates_y").change();
        addPointToPoiLayer(corX, corY, 'Vámi vybraná poloha záměru');
        let xhr = new XMLHttpRequest();
        xhr.open('POST', '/oznameni/get-katastr-from-point');
        xhr.setRequestHeader('Content-type', 'application/json');
        //xhr.setRequestHeader('csrfmiddlewaretoken', '{{ csrf_token }}' );
        xhr.onload = function () {
            // do something to response
            console.log(JSON.parse(this.responseText).cadastre);
            document.getElementById('katastr_name').innerHTML=JSON.parse(this.responseText).cadastre;
        };
        xhr.send(JSON.stringify({ 'corY': corY,'corX': corX }))

    } else {
        var zoom=2;
        if(map.getZoom()<10) zoom+=2;
        else if(map.getZoom()<13) zoom+=1;

        map.setView(e.latlng, map.getZoom() + zoom);
        //console.log("Your zoom is: "+map.getZoom())
    }
});
