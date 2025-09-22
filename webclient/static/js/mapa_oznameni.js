map.on('click', function (e) {
    if (!global_measuring_toolbox._measuring) {
        var addPointToPoiLayer = (point_leaf, text) => {
            L.marker(point_leaf,{icon: pinIconRedProject}).bindPopup(text).addTo(poi);
        }
        poi.clearLayers();
        let [x1, x2] = amcr_static_coordinate_precision_wgs84([e.latlng.lng, e.latlng.lat]);
        if (x1 >= 12.06 && x1 <= 18.87 && x2 >= 48.55 && x2 <= 51.08)
            if (map.getZoom() > 11) {
                document.getElementById('id_coordinate_x1').value = x1
                document.getElementById('id_coordinate_x2').value = x2
                point_leaf=[x2,x1]
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
                var zoom = 1;
                if (map.getZoom() < 6) zoom += 2;
                else if (map.getZoom() < 9) zoom += 1;

                map.setView(e.latlng, map.getZoom() + zoom);
            }
    }
});

// Načtení stavu při načtení stránky
loadMapState('oznameni');
// Připojení eventů pro sledování změn
addEventLayerChange('oznameni');