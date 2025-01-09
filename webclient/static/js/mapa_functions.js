 function saveMapState(prefix) {
    const mapState = {
        activeBaseLayer: Object.keys(baseLayers).find(name => map.hasLayer(baseLayers[name])), // Název aktivní základní vrstvy
        activeOverlays: Object.keys(overlays).filter(name => map.hasLayer(overlays[name]))     // Seznam aktivních overlay vrstev
    };

    // Uložení celého objektu jako JSON s prefixem
    localStorage.setItem(`${prefix}_mapState`, JSON.stringify(mapState));
}

function loadMapState(prefix) {
    const savedState = localStorage.getItem(`${prefix}_mapState`);
    if (savedState) {
        Object.values(baseLayers).forEach(layer => {
            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        });
        Object.values(overlays).forEach(layer => {
            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        });
        const mapState = JSON.parse(savedState);

        // Obnova základní vrstvy
        if (mapState.activeBaseLayer && baseLayers[mapState.activeBaseLayer]) {
            map.addLayer(baseLayers[mapState.activeBaseLayer]);
        }

        // Obnova overlay vrstev
        if (mapState.activeOverlays) {
            mapState.activeOverlays.forEach(layerName => {
                if (overlays[layerName]) {
                    map.addLayer(overlays[layerName]);
                }
            });
        }
    }
}

function addEventLayerChange(prefix) {
    map.on('overlayadd', () => saveMapState(prefix));
    map.on('overlayremove', () => saveMapState(prefix));
    map.on('baselayerchange', () => saveMapState(prefix));
}

