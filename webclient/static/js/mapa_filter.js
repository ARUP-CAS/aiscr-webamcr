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
    var mapLayerName = sectionEl.getAttribute("data-map-layer");
    var geomInput = document.getElementById("geom_filter");

    var heatmapOptions = typeof settings_heatmap_options !== "undefined" ? settings_heatmap_options : {};
    var heatLayer = new HeatmapOverlay(heatmapOptions);
    var boundsLock = null;
    var mapInitialized = false;

    // Datové vrstvy workflow – stejné pojmenování i ovládání jako v detailních mapách.
    // Sdílený markercluster + subgroupy: body se shlukují, polygony/linie jdou do stejné vrstvy.
    var mcg = L.markerClusterGroup({ disableClusteringAtZoom: 20 }).addTo(map);

    function makeDataLayer() {
        var group = L.featureGroup.subGroup(mcg);
        map.addLayer(group);
        return group;
    }

    var dataLayers = {}; // popisek vrstvy -> vrstva (jde do ovládání vrstev)
    var projektStavLayers = null; // stav projektu -> vrstva (jen workflow projekty)
    var defaultDataLayer = null; // vrstva pro ostatní workflow

    if (mapLayerName === "projekt") {
        var p1 = makeDataLayer();
        var p2 = makeDataLayer();
        var p3 = makeDataLayer();
        var p46 = makeDataLayer();
        var p78 = makeDataLayer();
        dataLayers[map_translations["projektyP1"]] = p1;
        dataLayers[map_translations["projektyP2"]] = p2;
        dataLayers[map_translations["projektyP3"]] = p3;
        dataLayers[map_translations["projektyP46"]] = p46;
        dataLayers[map_translations["projektyP78"]] = p78;
        projektStavLayers = { 1: p1, 2: p2, 3: p3, 4: p46, 5: p46, 6: p46, 7: p78, 8: p78 };
    } else if (mapLayerName === "pas") {
        defaultDataLayer = makeDataLayer();
        dataLayers[map_translations["samostatneNalezy"]] = defaultDataLayer;
    } else if (mapLayerName === "akce" || mapLayerName === "lokalita") {
        defaultDataLayer = makeDataLayer();
        dataLayers[map_translations["pian"]] = defaultDataLayer;
    } else if (mapLayerName === "3d") {
        defaultDataLayer = makeDataLayer();
        dataLayers[map_translations["Library3D"]] = defaultDataLayer;
    }

    // Přestavba ovládání vrstev: podklady + ČÚZK/NPÚ + datové vrstvy workflow.
    // Vypadnou vrstvy vázané na konkrétní záznam i prázdná „lokalizace“ z basic_functions.
    if (typeof global_map_layers !== "undefined" && global_map_layers) {
        global_map_layers.remove(map);
    }
    var controlOverlays = {};
    controlOverlays[map_translations["cuzkKatastralniMapa"]] = cuzkWMS;
    controlOverlays[map_translations["cuzkKatastralniUzemi"]] = cuzkWMS2;
    controlOverlays[map_translations["npuPamatkovaOchrana"]] = npuOchrana;
    Object.keys(dataLayers).forEach(function (name) {
        controlOverlays[name] = dataLayers[name];
    });
    L.control.layers(baseLayers, controlOverlays).addTo(map);

    // cílová datová vrstva pro daný prvek (u projektů podle stavu)
    function targetLayerFor(point) {
        if (projektStavLayers) {
            return projektStavLayers[point.stav] || null;
        }
        return defaultDataLayer;
    }

    function clearDataLayers() {
        Object.keys(dataLayers).forEach(function (name) {
            dataLayers[name].clearLayers();
        });
    }

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

    // koš v toolbaru maže výběr rovnou jedním klikem (bez režimu mazání Save/Cancel/Clear);
    // po smazání se musí vyprázdnit i skryté pole #geom_filter, jinak by se dál filtrovalo
    if (L.EditToolbar && L.EditToolbar.Delete && !L.EditToolbar.Delete.prototype._amcrInstantDelete) {
        L.EditToolbar.Delete.prototype._amcrInstantDelete = true;
        L.EditToolbar.Delete.prototype.enable = function () {
            if (this._hasAvailableLayers && !this._hasAvailableLayers()) {
                return;
            }
            this._deletedLayers = new L.LayerGroup();
            this.removeAllLayers();
            updateGeomFilter();
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

    function renderPoint(wkt, identCely, layerType, target) {
        var latlng = geomToLatLng(wkt);
        if (!latlng) {
            return;
        }
        L.marker(latlng, { icon: pointIconForType(layerType) })
            .bindTooltip(identCely, { sticky: true })
            .bindPopup(popupLink(layerType, identCely))
            .addTo(target);
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

    // PIAN (akce/lokalita): skutečná geometrie (polygon/linie/bod) jako v náhledu akce + pin v repr. bodě.
    // Popis i chování po kliknutí je shodné s mapou v detailu: tooltip „ident (přesnost)“ a popup se
    // seznamem dokumentačních jednotek, který dotáhne onMarkerClick z mapa_basic_functions.js.
    function renderPian(wkt, identCely, target, presnost) {
        var style = { color: "rgb(151, 0, 156)" };
        var popis = presnost ? identCely + " (" + presnost + ")" : identCely;
        var shape = null;
        if (wkt.indexOf("POLYGON") !== -1) {
            shape = L.polygon(wktPartToLatLngs(wkt, "(("), style);
        } else if (wkt.indexOf("LINESTRING") !== -1) {
            shape = L.polyline(wktPartToLatLngs(wkt, "("), style);
        }
        if (shape) {
            bindPianPopup(shape.bindTooltip(popis, { sticky: true }), identCely).addTo(target);
        }
        var latlng = geomToLatLng(wkt);
        if (latlng) {
            bindPianPopup(
                L.marker(latlng, { icon: pointIconForType("pian") }).bindTooltip(popis, { sticky: true }),
                identCely
            ).addTo(target);
        }
    }

    // popup s dokumentačními jednotkami PIANu (stejně jako v detailní mapě); bez onMarkerClick
    // zůstane aspoň odkaz na samotný PIAN
    function bindPianPopup(layer, identCely) {
        if (typeof onMarkerClick === "function") {
            return layer.bindPopup("").on("click", onMarkerClick.bind(null, identCely));
        }
        return layer.bindPopup(popupLink("pian", identCely));
    }

    function renderDetail(points) {
        points.forEach(function (i) {
            var target = targetLayerFor(i);
            if (!i.geom || !target) {
                return;
            }
            if (i.type === "pian") {
                renderPian(i.geom, i.ident_cely, target, i.presnost);
            } else {
                renderPoint(i.geom, i.ident_cely, i.type, target);
            }
        });
    }

    function renderHeat(heats) {
        var heatPoints = [];
        var maxHeat = 0;
        heats.forEach(function (i) {
            if (!i.geom) {
                return;
            }
            var match = i.geom.match(/POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)/i);
            if (!match) {
                return;
            }
            if (i.pocet > maxHeat) {
                maxHeat = i.pocet;
            }
            heatPoints.push({ lat: parseFloat(match[2]), lng: parseFloat(match[1]), count: i.pocet });
        });
        heatLayer = new HeatmapOverlay(heatmapOptions);
        heatLayer.setData({ max: maxHeat, data: heatPoints });
        map.addLayer(heatLayer);
    }

    // klíč výřezu ze všech čtyř rohů a zoomu – aby se přeskočilo jen skutečně nezměněné zobrazení
    // (porovnání pouhého topLeft by vynechalo načtení při změně samotného zoomu)
    function boundsKey(bounds, zoom) {
        return ["topLeft", "topRight", "bottomRight", "bottomLeft"]
            .map(function (corner) {
                return bounds[corner].lat.toFixed(6) + "," + bounds[corner].lng.toFixed(6);
            })
            .join("|") + "@" + zoom;
    }

    function loadMapData() {
        if (!endpoint) {
            return;
        }
        var bounds = getRotatedBounds();
        var zoom = map.getZoom();
        var key = boundsKey(bounds, zoom);
        if (boundsLock === key) {
            return;
        }
        boundsLock = key;

        // Odpověď z neaktuálního výřezu zahodíme – pomalejší starší požadavek by jinak přepsal
        // novější data. Běžící požadavek záměrně nerušíme (abort): server by dostal broken pipe.
        function jeStale() {
            return boundsLock !== key;
        }

        var xhr = new XMLHttpRequest();
        xhr.open("POST", endpoint);
        xhr.setRequestHeader("Content-type", "application/json");
        if (typeof global_csrftoken !== "undefined") {
            xhr.setRequestHeader("X-CSRFToken", global_csrftoken);
        }
        map.spin(true);
        xhr.onload = function () {
            map.spin(false);
            if (jeStale()) {
                return; // mezitím se výřez změnil, data už nejsou aktuální
            }
            if (this.status < 200 || this.status >= 300) {
                boundsLock = null; // ať se při dalším pohybu zkusí načíst znovu
                if (typeof console !== "undefined") {
                    console.error("mapa_filter: načtení dat selhalo (HTTP " + this.status + ")");
                }
                return;
            }
            // nejdřív parsujeme a teprve po úspěchu maž vrstvy – ať při chybné odpovědi
            // nezůstane mapa prázdná; boundsLock resetujeme, aby šlo načtení zopakovat
            var res;
            try {
                res = JSON.parse(this.responseText);
            } catch (e) {
                boundsLock = null;
                if (typeof console !== "undefined") {
                    console.error("mapa_filter: odpověď serveru se nepodařilo zpracovat", e);
                }
                return;
            }
            try {
                clearDataLayers();
                map.removeLayer(heatLayer);
                if (res.algorithm === "detail") {
                    renderDetail(res.points || []);
                } else {
                    renderHeat(res.heat || []);
                }
            } catch (e) {
                boundsLock = null;
                if (typeof console !== "undefined") {
                    console.error("mapa_filter: chyba při vykreslování dat", e);
                }
            }
        };
        xhr.onerror = function () {
            map.spin(false);
            if (jeStale()) {
                return;
            }
            boundsLock = null;
            if (typeof console !== "undefined") {
                console.error("mapa_filter: síťová chyba při načítání dat");
            }
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
