 function saveMapState(prefix,type,e) {
    let savedState, mapState; 
    savedState = localStorage.getItem(`${prefix}_mapState`);
    if(!savedState) {
        mapState = {};
    }
    else mapState = JSON.parse(savedState);
    if(type=="activeOverlays"){       
        mapState["activeOverlays"]= Object.keys(overlays).filter(name => map.hasLayer(overlays[name])) ;    // Seznam aktivních overlay vrstev
    }
    else if(type=="activeBaseLayer"){
        mapState["activeBaseLayer"]= Object.keys(baseLayers).find(name => map.hasLayer(baseLayers[name])); // Název aktivní základní vrstvy    
    }
    else if(type=="search"){
        mapState["search"]= e.key;     
    }
    // Uložení celého objektu jako JSON s prefixem
    localStorage.setItem(`${prefix}_mapState`, JSON.stringify(mapState));
}

function loadMapState(prefix) {
    const savedState = localStorage.getItem(`${prefix}_mapState`);
    if (savedState) {
        const mapState = JSON.parse(savedState);
        // Obnova základní vrstvy
        if (mapState.activeBaseLayer && baseLayers[mapState.activeBaseLayer]) {
            Object.values(baseLayers).forEach(layer => {
                if (map.hasLayer(layer)) {
                    map.removeLayer(layer);
                }
            });
            map.addLayer(baseLayers[mapState.activeBaseLayer]);
        }
        // Obnova overlay vrstev
        if (mapState.activeOverlays) {
            Object.values(overlays).forEach(layer => {
                if (map.hasLayer(layer)) {
                    map.removeLayer(layer);
                }
            });
            mapState.activeOverlays.forEach(layerName => {
                if (overlays[layerName]) {
                    map.addLayer(overlays[layerName]);
                }
            });
        }
        if(mapState.search)
        {
            searchControl.changeChooseTip(mapState.search);
	        searchControl.collapse();
        }
    }
}

function addEventLayerChange(prefix) {
    map.on('overlayadd overlayremove', () => saveMapState(prefix,"activeOverlays"));
    map.on('baselayerchange', () => saveMapState(prefix,"activeBaseLayer"));
    map.on('search:changeChooseTip', function (e) {saveMapState(prefix,"search",e)});
}

