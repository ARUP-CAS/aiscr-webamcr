var poi_other = L.layerGroup();
var poi = L.layerGroup();
map.addLayer(poi);

var addPointToPoiLayer = (lat, long, text) => {
        L.marker([lat, long]).bindPopup(text).addTo(poi);
}

map.on('click', function (e) {
    if(!global_measuring_toolbox._measuring){
        poi.clearLayers();
        let corX = e.latlng.lat;
        let corY = e.latlng.lng;
        if(corY>=12.2401111182 && corY<=18.8531441586 && corX>=48.5553052842 && corX<=51.1172677679)
        if (map.getZoom() > 15) {
            document.getElementById('id_latitude').value = corX
            document.getElementById('id_longitude').value = corY
            //$("#detector_coordinates_x").change();
            //$("#detector_coordinates_y").change();
            addPointToPoiLayer(corX, corY, 'Vámi vybraná poloha záměru');
            let xhr = new XMLHttpRequest();
            xhr.open('POST', '/oznameni/get-katastr-from-point');
            xhr.setRequestHeader('Content-type', 'application/json');
            if (typeof global_csrftoken !== 'undefined') {
                xhr.setRequestHeader('X-CSRFToken', global_csrftoken );
            }
            xhr.onload = function () {
                // do something to response
                //console.log(JSON.parse(this.responseText).cadastre);
                if(JSON.parse(this.responseText).cadastre=="None"){
                    alert("Neplatny bod, klikli jste mimo území ČR")
                    //console.log("Neplatny bod, klikli jste mimo území ČR")
                } else {
                    const uzemi = document.getElementById('id_katastralni_uzemi');
                    uzemi.value=JSON.parse(this.responseText).cadastre;
                }
            };
            xhr.send(JSON.stringify({ 'corY': corY,'corX': corX }))

        } else {
            var zoom=2;
            if(map.getZoom()<10) zoom+=2;
            else if(map.getZoom()<13) zoom+=1;

            map.setView(e.latlng, map.getZoom() + zoom);
            //console.log("Your zoom is: "+map.getZoom())
        }
    }
});
