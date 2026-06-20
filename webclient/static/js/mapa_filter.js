/*
 * mapa_filter.js — mapový výběr/filtr v záložce filtru výpisu.
 * Výběr obdélníkem → WKT do #geom_filter (odešle se s filtrem); datová vrstva se načítá
 * z #mapaCollapse[data-map-endpoint] podle výřezu. Globální `map` vytváří basic_functions skript.
 */
(function () {
    "use strict";

    if (typeof map === "undefined" || !map) {
        return;
    }

    var sectionEl = document.getElementById("mapaCollapse");
    if (!sectionEl) {
        return;
    }

    var endpoint = sectionEl.getAttribute("data-map-endpoint");
    var geomInput = document.getElementById("geom_filter");

    // body se shlukují (markercluster), polygony/linie jdou do samostatné vrstvy
    var poiLayer = (typeof L.markerClusterGroup !== "undefined"
        ? L.markerClusterGroup({ disableClusteringAtZoom: 20 })
        : L.layerGroup()).addTo(map);
    var shapeLayer = L.layerGroup().addTo(map);
    var heatmapOptions = typeof settings_heatmap_options !== "undefined" ? settings_heatmap_options : {};
    var heatLayer = new HeatmapOverlay(heatmapOptions);
    var boundsLock = null;
    var mapInitialized = false;

    // Lokalizace popisků nástroje pro kreslení (leaflet-draw)
    if (typeof draw_translations !== "undefined" && L.drawLocal) {
        L.drawLocal.draw.toolbar.buttons.rectangle = draw_translations.rectangle;
        L.drawLocal.draw.handlers.rectangle.tooltip.start = draw_translations.rectangleStart;
        L.drawLocal.draw.handlers.simpleshape.tooltip.end = draw_translations.rectangleEnd;
        L.drawLocal.edit.toolbar.buttons.remove = draw_translations.deleteSelection;
        L.drawLocal.edit.toolbar.buttons.removeDisabled = draw_translations.deleteSelection;
    }

    // Výchozí leaflet-draw obdélník staví z LatLngBounds → na pootočené S-JTSK mapě se kreslí šikmo.
    // Přepíšeme kreslení do obrazovkových (layer) bodů, aby byl výběr zarovnaný s mřížkou.
    if (L.Draw && L.Draw.Rectangle && !L.Draw.Rectangle.prototype._amcrScreenAligned) {
        L.Draw.Rectangle.prototype._amcrScreenAligned = true;
        L.Draw.Rectangle.prototype._screenAlignedCorners = function (latlng) {
            var a = this._map.latLngToLayerPoint(this._startLatLng);
            var b = this._map.latLngToLayerPoint(latlng);
            var minX = Math.min(a.x, b.x);
            var maxX = Math.max(a.x, b.x);
            var minY = Math.min(a.y, b.y);
            var maxY = Math.max(a.y, b.y);
            return [
                this._map.layerPointToLatLng([minX, minY]),
                this._map.layerPointToLatLng([maxX, minY]),
                this._map.layerPointToLatLng([maxX, maxY]),
                this._map.layerPointToLatLng([minX, maxY])
            ];
        };
        L.Draw.Rectangle.prototype._drawShape = function (latlng) {
            var corners = this._screenAlignedCorners(latlng);
            if (!this._shape) {
                this._shape = new L.Polygon(corners, this.options.shapeOptions);
                this._map.addLayer(this._shape);
            } else {
                this._shape.setLatLngs(corners);
            }
        };
        L.Draw.Rectangle.prototype._fireCreatedEvent = function () {
            var poly = new L.Polygon(this._shape.getLatLngs(), this.options.shapeOptions);
            L.Draw.SimpleShape.prototype._fireCreatedEvent.call(this, poly);
        };
    }

    // koš v toolbaru maže výběr rovnou jedním klikem (bez režimu mazání Save/Cancel/Clear)
    if (L.EditToolbar && L.EditToolbar.Delete && !L.EditToolbar.Delete.prototype._amcrInstantDelete) {
        L.EditToolbar.Delete.prototype._amcrInstantDelete = true;
        L.EditToolbar.Delete.prototype.enable = function () {
            if (this._hasAvailableLayers && !this._hasAvailableLayers()) {
                return;
            }
            this._deletedLayers = new L.LayerGroup();
            this.removeAllLayers();
        };
    }

    var drawnItems = new L.FeatureGroup().addTo(map);
    var drawControl = new L.Control.Draw({
        position: "topleft",
        draw: {
            rectangle: { shapeOptions: { color: "#ba0d27", weight: 2 } },
            polygon: false,
            polyline: false,
            circle: false,
            marker: false,
            circlemarker: false
        },
        edit: {
            featureGroup: drawnItems,
            edit: false,
            remove: true
        }
    });
    map.addControl(drawControl);

    // nakreslený obdélník → WKT POLYGON (EPSG:4326)
    function layerToWkt(layer) {
        var rings = layer.getLatLngs();
        var ring = Array.isArray(rings[0]) ? rings[0] : rings;
        if (!ring || ring.length < 3) {
            return "";
        }
        var coords = ring.map(function (ll) {
            return ll.lng + " " + ll.lat;
        });
        coords.push(ring[0].lng + " " + ring[0].lat);
        return "POLYGON((" + coords.join(",") + "))";
    }

    function updateGeomFilter() {
        if (!geomInput) {
            return;
        }
        var layers = drawnItems.getLayers();
        if (layers.length > 0) {
            geomInput.value = layerToWkt(layers[layers.length - 1]);
        } else {
            geomInput.value = "";
        }
    }

    map.on(L.Draw.Event.CREATED, function (e) {
        drawnItems.clearLayers();
        drawnItems.addLayer(e.layer);
        updateGeomFilter();
    });
    map.on(L.Draw.Event.EDITED, updateGeomFilter);
    map.on(L.Draw.Event.DELETED, updateGeomFilter);

    // překreslení výběru z uložené WKT hodnoty (po reloadu s aktivním filtrem)
    function restoreSelection() {
        if (!geomInput || !geomInput.value) {
            return;
        }
        var match = geomInput.value.match(/\(\((.+)\)\)/);
        if (!match) {
            return;
        }
        var latlngs = match[1].split(",").map(function (pair) {
            var xy = pair.trim().split(/\s+/);
            return [parseFloat(xy[1]), parseFloat(xy[0])];
        });
        if (latlngs.length >= 3) {
            var poly = L.polygon(latlngs, { color: "#ba0d27", weight: 2 });
            drawnItems.addLayer(poly);
        }
    }

    function getRotatedBounds() {
        var pixelBounds = map.getPixelBounds();
        return {
            topLeft: map.unproject(pixelBounds.getTopLeft()),
            topRight: map.unproject(pixelBounds.getTopRight()),
            bottomRight: map.unproject(pixelBounds.getBottomRight()),
            bottomLeft: map.unproject(pixelBounds.getBottomLeft())
        };
    }

    // ikona pinu podle typu: PAS = žlutý pin, projekt = žlutý, PIAN (akce/lokalita) i 3D = fialový
    function pointIconForType(layerType) {
        if (layerType === "pas" && typeof pinIconYellowPin !== "undefined") {
            return pinIconYellowPin;
        }
        if (layerType === "projekt" && typeof pinIconYellow !== "undefined") {
            return pinIconYellow;
        }
        if (layerType === "pian" && typeof pinIconPurplePoint !== "undefined") {
            return pinIconPurplePoint;
        }
        if (layerType === "3d" && typeof pinIconPurple3D !== "undefined") {
            return pinIconPurple3D;
        }
        return typeof pinIconPurplePin !== "undefined" ? pinIconPurplePin : new L.Icon.Default();
    }

    // reprezentativní bod libovolné WKT geometrie = průměr všech vrcholů (null pro prázdnou)
    function geomToLatLng(wkt) {
        var open = wkt.indexOf("(");
        if (open === -1) {
            return null;
        }
        var sumLat = 0;
        var sumLng = 0;
        var n = 0;
        wkt
            .substring(open)
            .replace(/[()]/g, " ")
            .split(",")
            .forEach(function (token) {
                var xy = token.trim().split(/\s+/);
                var lng = parseFloat(xy[0]);
                var lat = parseFloat(xy[1]);
                if (!isNaN(lng) && !isNaN(lat)) {
                    sumLng += lng;
                    sumLat += lat;
                    n += 1;
                }
            });
        if (n === 0) {
            return null;
        }
        return amcr_static_coordinate_precision_wgs84([sumLat / n, sumLng / n]);
    }

    function detailUrlFor(layerType, identCely) {
        if (layerType === "pas") {
            return "/pas/detail/" + identCely;
        }
        if (layerType === "3d") {
            return "/dokument/model/detail/" + identCely;
        }
        return "/id/" + identCely;
    }

    function popupLink(layerType, identCely) {
        return '<a href="' + detailUrlFor(layerType, identCely) + '" target="_blank">' + identCely + "</a>";
    }

    function renderPoint(wkt, identCely, layerType) {
        var latlng = geomToLatLng(wkt);
        if (!latlng) {
            return;
        }
        L.marker(latlng, { icon: pointIconForType(layerType) })
            .bindTooltip(identCely, { sticky: true })
            .bindPopup(popupLink(layerType, identCely))
            .addTo(poiLayer);
    }

    // souřadnice prvního prstence/části geometrie ("(" pro linii, "((" pro polygon)
    function wktPartToLatLngs(wkt, marker) {
        return wkt
            .substring(wkt.indexOf(marker) + marker.length)
            .split(")")[0]
            .split(",")
            .map(function (pair) {
                var xy = pair.trim().replace(/[()]/g, "").split(/\s+/);
                return amcr_static_coordinate_precision_wgs84([xy[1], xy[0]]);
            });
    }

    // PIAN (akce/lokalita): skutečná geometrie (polygon/linie/bod) jako v náhledu akce + pin v repr. bodě
    function renderPian(wkt, identCely) {
        var style = { color: "rgb(151, 0, 156)" };
        var shape = null;
        if (wkt.indexOf("POLYGON") !== -1) {
            shape = L.polygon(wktPartToLatLngs(wkt, "(("), style);
        } else if (wkt.indexOf("LINESTRING") !== -1) {
            shape = L.polyline(wktPartToLatLngs(wkt, "("), style);
        }
        if (shape) {
            shape.bindTooltip(identCely, { sticky: true }).bindPopup(popupLink("pian", identCely)).addTo(shapeLayer);
        }
        var latlng = geomToLatLng(wkt);
        if (latlng) {
            L.marker(latlng, { icon: pointIconForType("pian") })
                .bindTooltip(identCely, { sticky: true })
                .bindPopup(popupLink("pian", identCely))
                .addTo(poiLayer);
        }
    }

    function renderDetail(points) {
        points.forEach(function (i) {
            if (!i.geom) {
                return;
            }
            if (i.type === "pian") {
                renderPian(i.geom, i.ident_cely);
            } else {
                renderPoint(i.geom, i.ident_cely, i.type);
            }
        });
    }

    function renderHeat(heats) {
        var heatPoints = [];
        var maxHeat = 0;
        heats.forEach(function (i) {
            var geom = i.geom.split("(")[1].split(")")[0].split(" ");
            if (i.pocet > maxHeat) {
                maxHeat = i.pocet;
            }
            heatPoints.push({ lat: parseFloat(geom[1]), lng: parseFloat(geom[0]), count: i.pocet });
        });
        heatLayer = new HeatmapOverlay(heatmapOptions);
        heatLayer.setData({ max: maxHeat, data: heatPoints });
        map.addLayer(heatLayer);
    }

    function loadMapData() {
        if (!endpoint) {
            return;
        }
        var bounds = getRotatedBounds();
        var zoom = map.getZoom();
        if (boundsLock && boundsLock.topLeft && bounds.topLeft.equals(boundsLock.topLeft)) {
            return;
        }
        boundsLock = bounds;
        var xhr = new XMLHttpRequest();
        xhr.open("POST", endpoint);
        xhr.setRequestHeader("Content-type", "application/json");
        if (typeof global_csrftoken !== "undefined") {
            xhr.setRequestHeader("X-CSRFToken", global_csrftoken);
        }
        map.spin(true);
        xhr.onload = function () {
            try {
                poiLayer.clearLayers();
                shapeLayer.clearLayers();
                map.removeLayer(heatLayer);
                var res = JSON.parse(this.responseText);
                if (res.algorithm === "detail") {
                    renderDetail(res.points || []);
                } else {
                    renderHeat(res.heat || []);
                }
            } catch (e) {
                if (typeof console !== "undefined") {
                    console.log(e);
                }
            }
            map.spin(false);
        };
        xhr.onerror = function () {
            map.spin(false);
        };
        xhr.send(JSON.stringify({ bounds: bounds, zoom: zoom }));
    }

    map.on("moveend", function () {
        if (mapInitialized) {
            loadMapData();
        }
    });

    // rozsah ČR pro výchozí zobrazení bez výběru
    var czBounds = L.latLngBounds([48.55, 12.09], [51.06, 18.87]);

    // mapa se inicializuje až při prvním rozbalení sekce (Leaflet potřebuje viditelný kontejner)
    function initMapSection() {
        map.invalidateSize();
        if (!mapInitialized) {
            mapInitialized = true;
            var selection = drawnItems.getLayers();
            map.fitBounds(selection.length > 0 ? drawnItems.getBounds() : czBounds);
            loadMapData();
        }
    }

    sectionEl.addEventListener("shown.bs.collapse", initMapSection);

    document.addEventListener("DOMContentLoaded", function () {
        if (geomInput && geomInput.value) {
            restoreSelection();
        }
    });
})();
