/** @format */

L.Control.EditCoordControl = L.Control.extend({
    options: {
        saveText: 'Uložit změny',
        stornoText: 'Storno',
        tooltipText: 'Klikněte pro vybrání bodu',
        tooltipSubText: '',
        titleText: 'Editovat souřadnice',
        modifyText: 'Upravit',
    },

    initialize: function (options) {

        this._active = false
        this._tempMarkers = []
        this._uneditedLayerProps = {}
        this._container = null
        this._epsg = null
        L.Util.setOptions(this, options)
    },

    onAdd: function (map) {
        this._map = map;
        this._container = L.DomUtil.create('a', 'leaflet-draw-edit-edit')
        this._container.href = '#'
        this._container.title = this.options.titleText;
        this._container.innerHTML =
            '<img src="../img/coord-edit.png" style="width:20px">'
        this._container.style.backgroundImage = 'none'
        this._container.style.background

        this.container1 = L.DomUtil.create('ul', 'leaflet-draw-actions')
        this.container1.innerHTML =
            `<li><a href="#" id="saveChanges" title="${this.options.saveText}">${this.options.saveText}</a></li><li><a href="#" id="cancelChanges" title="${this.options.stornoText}">${this.options.stornoText}</a></li>`
        this.container1.style.display = 'none'
        this.container1.style.top = '32px'

        let drawSections = document.querySelectorAll('.leaflet-draw-toolbar')
        if (drawSections.length > 1) {
            drawSections[1].appendChild(this._container)
            drawSections[1].parentElement.appendChild(this.container1)
        } else {
            map.getContainer().appendChild(this._container)
        }
        this._createCoordDialog()

        this._container.onclick = function () {
            if (this._active === false) {
                this._map.fire('editCoord:start')

                this.activate(map)
            } else {
                this.deactivate()
            }
        }.bind(this)

        // Navázání událostí na tlačítka Uložit a Storno
        document.getElementById('saveChanges').onclick = function (e) {
            e.preventDefault();

            this.deactivate(true);
        }.bind(this)

        document.getElementById('cancelChanges').onclick = function (e) {
            e.preventDefault();
            this.deactivate();
        }.bind(this)

        return this._container
    },

    activate: function () {
        this._active = true
        this.container1.style.display = 'block'
        this._createTooltip()
        drawnItems.eachLayer((layer) => {
            this._saveOriginalCoordinates(layer) // Uložení původních souřadnic

            if (layer instanceof L.Polygon || layer instanceof L.Polyline) {
                let latlngs =
                    layer instanceof L.Polygon
                        ? layer.getLatLngs()[0]
                        : layer.getLatLngs()
                latlngs.forEach((latlng, index) => {
                    let squareMarker = L.marker(latlng, {
                        icon: this._createCustomMarker(latlng),
                    }).addTo(this._map)
                    this._tempMarkers.push(squareMarker)
                    squareMarker.off('click')
                    squareMarker.on('click', () =>{
                        this._lineMarkerClick(
                            squareMarker,
                            latlng,
                            index,
                            layer,
                            latlngs
                        )}
                    )
                })
            } else if (layer instanceof L.Marker) {
                layer.off('click')
                layer.on('click', () => {this._pointMarkerClick(layer)})
            }
        })
    },

    deactivate: function (save=false) {
        this._active = false
        this.container1.style.display = 'none'
        this._tempMarkers.forEach((marker) => {
            this._map.removeLayer(marker)
            marker=null
        })        
        this._tempMarkers = []
        this._deactivateTooltip()
        if(save==false){
            this._restoreOriginalCoordinates();
        }
        else{       
            this._map.fire('editCoord:save',{epsg: this._epsg});
        }
        this._uneditedLayerProps = {} // Vyprázdnění uložených souřadnic, aby nebylo možné je vrátit
    },

    _pointMarkerClick: function (layer) {
        let latlng = layer.getLatLng()
        this._fillInputContainer(latlng)
        L.popup()
            .setLatLng(latlng)
            .setContent(this._inputcontainer)
            .openOn(this._map)
        this._inputcontainer.latlng=latlng;
        this._inputcontainer.layer=layer;
     },

    _lineMarkerClick: function (squareMarker, latlng, index, layer, latlngs) {
        this._fillInputContainer(latlng)
        this._deactivateTooltip()
        let popup = L.popup()
            .setLatLng(latlng)
            .setContent(this._inputcontainer)
            .openOn(this._map);
        popup.on("remove", function() {
                this._createTooltip();
            },this);
        this._inputcontainer.squareMarker=squareMarker;
        this._inputcontainer.latlng=latlng;
        this._inputcontainer.index=index;
        this._inputcontainer.layer=layer;
        this._inputcontainer.latlngs=latlngs;      
    },

    _saveOriginalCoordinates: function (layer) {
        let id = L.Util.stamp(layer)

        if (!this._uneditedLayerProps[id]) {
            // Polyline, Polygon or Rectangle
            if (
                layer instanceof L.Polyline ||
                layer instanceof L.Polygon ||
                layer instanceof L.Rectangle
            ) {
                this._uneditedLayerProps[id] = {
                    latlngs: L.LatLngUtil.cloneLatLngs(layer.getLatLngs()),
                }
            } else if (layer instanceof L.Circle) {
                this._uneditedLayerProps[id] = {
                    latlng: L.LatLngUtil.cloneLatLng(layer.getLatLng()),
                    radius: layer.getRadius(),
                }
            } else if (
                layer instanceof L.Marker ||
                layer instanceof L.CircleMarker
            ) {
                // Marker
                this._uneditedLayerProps[id] = {
                    latlng: L.LatLngUtil.cloneLatLng(layer.getLatLng()),
                }
            }
        }
    },
    _restoreOriginalCoordinates: function () {
        drawnItems.eachLayer((layer) => {
            let id = L.Util.stamp(layer)
            layer.edited = false
            if (this._uneditedLayerProps.hasOwnProperty(id)) {
                // Polyline, Polygon or Rectangle
                if (
                    layer instanceof L.Polyline ||
                    layer instanceof L.Polygon ||
                    layer instanceof L.Rectangle
                ) {
                    layer.setLatLngs(this._uneditedLayerProps[id].latlngs)
                } else if (layer instanceof L.Circle) {
                    layer.setLatLng(this._uneditedLayerProps[id].latlng)
                    layer.setRadius(this._uneditedLayerProps[id].radius)
                } else if (
                    layer instanceof L.Marker ||
                    layer instanceof L.CircleMarker
                ) {
                    // Marker or CircleMarker
                    layer.setLatLng(this._uneditedLayerProps[id].latlng)
                }

                layer.fire('revert-edited', {layer: layer});
            }
        })
    },
    _createCoordDialog: function () {
        this._inputcontainer = L.DomUtil.create(
            'div',
            'uiElement input uiHidden'
        )
        this._inputcontainer.style="text-align: right;" ;
        this._inputcontainerWGS84 = L.DomUtil.create(
            'div',
            '',
            this._inputcontainer
        )
        this._inputcontainerJTSK = L.DomUtil.create(
            'div',
            '',
            this._inputcontainer
        )
        let xSpan, ySpan

        xSpan = L.DomUtil.create('span', '', this._inputcontainerWGS84)
        this._inputX = this._createInput(
            'coordInput',
            this._inputcontainerWGS84
        )
        ySpan = L.DomUtil.create('span', '', this._inputcontainerWGS84)
        this._inputY = this._createInput(
            'coordInput',
            this._inputcontainerWGS84
        )

        xSpanJTSK = L.DomUtil.create('span', '', this._inputcontainerJTSK)
        this._inputXJTSK = this._createInput(
            'coordInput',
            this._inputcontainerJTSK
        )
        ySpanJTSK = L.DomUtil.create('span', '', this._inputcontainerJTSK)
        this._inputYJTSK = this._createInput(
            'coordInput',
            this._inputcontainerJTSK
        )
        xSpan.innerHTML = ' E '
        ySpan.innerHTML = ' N '
        xSpanJTSK.innerHTML = ' X '
        ySpanJTSK.innerHTML = ' Y '
        this._buttonSubmit = L.DomUtil.create(
            'button',
            '',
            this._inputcontainer
        ) // '<button type="button" id="updateMarkerButton">Upravit</button>' +
        this._buttonSubmit.innerHTML = this.options.modifyText
        this._buttonSubmit.style="margin-top: 2px;"
        this._buttonSubmit.addEventListener('click', () => {
            this._buttonSubmitEvent();
        })
        L.DomEvent.on(this._inputX, 'keyup', this._handleKeypress, this)
        L.DomEvent.on(this._inputY, 'keyup', this._handleKeypress, this)
        L.DomEvent.on(this._inputXJTSK, 'keyup', this._handleKeypress, this)
        L.DomEvent.on(this._inputYJTSK, 'keyup', this._handleKeypress, this)
    },
    _createInput: function (classname, container) {
        let input = L.DomUtil.create('input', classname, container)
        input.type = 'text'
        L.DomEvent.disableClickPropagation(input)
        return input
    },
    _handleKeypress: function (e) {
        if (e.target == this._inputY || e.target == this._inputX) {
            let x = parseFloat(this._inputX.value)
            let y = parseFloat(this._inputY.value)
            if (x !== undefined && y !== undefined) {
                let coords = convertToJTSK(x, y)
                this._inputXJTSK.value = Math.round(coords[0] * 100) / 100
                this._inputYJTSK.value = Math.round(coords[1] * 100) / 100
                this._epsg=4326
            }
        } else {
            let x = parseFloat(this._inputXJTSK.value)
            let y = parseFloat(this._inputYJTSK.value)
            if (x !== undefined && y !== undefined) {
                let latlng = convertToWGS84(x, y)
                this._inputX.value =  Math.round(latlng[0] * 10000000) / 10000000
                this._inputY.value =  Math.round(latlng[1] * 10000000) / 10000000
                this._epsg=5514
            }
        }
    },
    _fillInputContainer: function (latlng) {
        this._inputX.value = Math.round(latlng.lng * 10000000) / 10000000 
        this._inputY.value = Math.round(latlng.lat * 10000000) / 10000000
        let coords = convertToJTSK(latlng.lng, latlng.lat)
        this._inputXJTSK.value = Math.round(coords[0] * 100) / 100
        this._inputYJTSK.value = Math.round(coords[1] * 100) / 100
    },
    _createTooltip: function () {
        this.tooltip = new L.Draw.Tooltip(this._map)
        this.tooltip.updateContent({
            text: this.options.tooltipText,
            subtext: this.options.tooltipSubText,
        })

        this._map
            .on('mousemove', this._onMouseMove, this)
            .on('touchmove', this._onMouseMove, this)
            .on('MSPointerMove', this._onMouseMove, this)
    },
    _deactivateTooltip: function () {
        this.tooltip.dispose()
		this.tooltip = null;
        this._map
            .off('mousemove', this._onMouseMove, this)
            .off('touchmove', this._onMouseMove, this)
            .off('MSPointerMove', this._onMouseMove, this)
    },

    _onMouseMove: function (e) {
        let pos = this._map.latLngToLayerPoint(e.latlng)
        tooltipContainer = this.tooltip._container
        if (this.tooltip) {
				tooltipContainer.style.visibility = 'inherit';
            L.DomUtil.setPosition(tooltipContainer, pos)
        }
        return this
    },
    _createCustomMarker: function (latlng) {
        return L.divIcon({
            className: 'custom-edit-coord-marker',
            iconSize: [12, 12],
            iconAnchor: [6, 6],
        })
    },
    _buttonSubmitEvent: function(e){
        let latlng=this._inputcontainer.latlng;
        let layer=this._inputcontainer.layer;
        if(layer instanceof L.Marker){
            latlng.lng = parseFloat(this._inputX.value);
            latlng.lat = parseFloat(this._inputY.value);
            layer.setLatLng(latlng);
            this._ensurePointVisible(latlng);
            this._map.closePopup();
        }
        else{
            let squareMarker=this._inputcontainer.squareMarker;            
            let index=this._inputcontainer.index;            
            let latlngs=this._inputcontainer.latlngs;

            let oldLatLng = L.latLng(latlng.lat, latlng.lng)
            latlng.lng = parseFloat(this._inputX.value)
            latlng.lat = parseFloat(this._inputY.value)
            
            latlngs[index].lat = latlng.lat
            latlngs[index].lng = latlng.lng

            if (layer instanceof L.Polygon) {
                layer.setLatLngs([latlngs])
            } else if (layer instanceof L.Polyline) {
                layer.setLatLngs(latlngs)
            }
            if (layer.intersects()) {
                // Kontrola křížení
                this._map.fire('editCoord:intersects')
                latlngs[index].lat = oldLatLng.lat
                latlngs[index].lng = oldLatLng.lng
                if (layer instanceof L.Polygon) {
                    layer.setLatLngs([latlngs])
                } else if (layer instanceof L.Polyline) {
                    layer.setLatLngs(latlngs)
                }
            } else {
                squareMarker.setLatLng([latlng.lat, latlng.lng])
                this._map.closePopup()
                this._ensurePointVisible(latlng);
            }

        }

    },
    _ensurePointVisible: function (latlng) {
        let bounds = this._map.getBounds();
        if (!bounds.contains(latlng)) {
            //this._map.panInside(latlng);
            let zoom=this._map.getZoom()
            this._map.setView(latlng, zoom) ;  
        }
    },

})
