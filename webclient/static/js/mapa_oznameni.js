var poi_other = L.layerGroup();
var poi = L.layerGroup();
map.addLayer(poi);

map.on('click', function (e) {
    if (!global_measuring_toolbox._measuring) {
        var addPointToPoiLayer = (point_leaf, text) => {
            L.marker(point_leaf,{icon: pinIconRedProject}).bindPopup(text).addTo(poi);
        }
        poi.clearLayers();
        let [x1, x2] = amcr_static_coordinate_precision_wgs84([e.latlng.lng, e.latlng.lat]);
        if (x1 >= 12.2401111182 && x1 <= 18.8531441586 && x2 >= 48.5553052842 && x2 <= 51.1172677679)
            if (map.getZoom() > 15) {
                document.getElementById('id_coordinate_x1').value = x1
                document.getElementById('id_coordinate_x2').value = x2
                point_leaf=[x2,x1]
                console.log(point_leaf)
                addPointToPoiLayer(point_leaf, [map_translations['lokalizaceZamer']]);  // 'Vámi vybraná poloha záměru'
                let xhr = new XMLHttpRequest();
                xhr.open('POST', '/oznameni/mapa-zjisti-katastr');
                xhr.setRequestHeader('Content-type', 'application/json');
                if (typeof global_csrftoken !== 'undefined') {
                    xhr.setRequestHeader('X-CSRFToken', global_csrftoken);
                }
                xhr.onload = function () {
                    if (JSON.parse(this.responseText).cadastre == "None") {
                        alert([map_translations['mimoCR']])  // "Neplatny bod, klikli jste mimo území ČR"
                    } else {
                        const uzemi = document.getElementById('id_katastralni_uzemi');
                        uzemi.value = JSON.parse(this.responseText).cadastre;
                    }
                };
                xhr.send(JSON.stringify({ 'x1': x1, 'x2': x2 }))

            } else {
                var zoom = 2;
                if (map.getZoom() < 10) zoom += 2;
                else if (map.getZoom() < 13) zoom += 1;

                map.setView(e.latlng, map.getZoom() + zoom);
            }
    }
});
