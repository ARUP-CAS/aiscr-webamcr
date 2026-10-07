//https://github.com/MrMufflon/Leaflet.Coordinates/blob/master/examples/demo.html
L.NumberFormatter = {
	round: function (num, dec, sep) {
		var res = L.Util.formatNum(num, dec) + "",
			numbers = res.split(".");
		if (numbers[1]) {
			var d = dec - numbers[1].length;
			for (; d > 0; d--) {
				numbers[1] += "0";
			}
			res = numbers.join(sep || ".");
		}
		return res;
	},

	toDMS: function (deg) {
		var d = Math.floor(Math.abs(deg));
		var minfloat = (Math.abs(deg) - d) * 60;
		var m = Math.floor(minfloat);
		var secfloat = (minfloat - m) * 60;
		var s = Math.round(secfloat);
		if (s == 60) {
			m++;
			s = "00";
		}
		if (m == 60) {
			d++;
			m = "00";
		}
		if (s < 10) {
			s = "0" + s;
		}
		if (m < 10) {
			m = "0" + m;
		}
		var dir = "";
		if (deg < 0) {
			dir = "-";
		}
		return ("" + dir + d + "&deg; " + m + "' " + s + "''");
	},

	createValidNumber: function (num, sep) {
		if (num && num.length > 0) {
			var numbers = num.split(sep || ".");
			try {
				var numRes = Number(numbers.join("."));
				if (isNaN(numRes)) {
					return undefined;
				}
				return numRes;
			} catch (e) {
				return undefined;
			}
		}
		return undefined;
	}
};
/*
 * L.Control.Coordinates is used for displaying current mouse coordinates on the map.
 */

L.Control.Coordinates = L.Control.extend({
	options: {
		position: 'bottomright',
		//decimals used if not using DMS or labelFormatter functions
		decimals: 4,
		//decimalseperator used if not using DMS or labelFormatter functions
		decimalSeperator: ".",
		//label templates for usage if no labelFormatter function is defined
		labelTemplateLat: "Lat: {y}",
		labelTemplateLng: "Lng: {x}",
		//label formatter functions
		labelFormatterLat: undefined,
		labelFormatterLng: undefined,
		//switch on/off input fields on click
		enableUserInput: true,
		//use Degree-Minute-Second
		useDMS: false,
		//if true lat-lng instead of lng-lat label ordering is used
		useLatLngOrder: false,
		//if true user given coordinates are centered directly
		centerUserCoordinates: false,
		//leaflet marker type
		markerType: L.marker,
		//leaflet marker properties
		markerProps: {}
	},

	onAdd: function (map) {
		this._map = map;

		var className = 'leaflet-control-coordinates',
			container = this._container = L.DomUtil.create('div', className),
			options = this.options;

		if (!L.Browser.touch) { //ToDo: zmenit/pridat
			L.DomEvent
				.disableClickPropagation(container)
				.disableScrollPropagation(container);
		} else {
			L.DomEvent.on(container, 'click', L.DomEvent.stopPropagation);
		}

		//label containers
		this._labelcontainer = L.DomUtil.create("div", "uiElement label", container);
		this._label = L.DomUtil.create("span", "labelFirst", this._labelcontainer);
		this._labelcontainer2 = L.DomUtil.create("div", "uiElement label", container);
		this._labelJTSK = L.DomUtil.create("span", "labeljtsk", this._labelcontainer2);


		//input containers
		this._inputcontainer = L.DomUtil.create("div", "uiElement input uiHidden", container);
		this._inputcontainerWGS84 = L.DomUtil.create("div", "", this._inputcontainer);
		this._inputcontainerJTSK = L.DomUtil.create("div", "", this._inputcontainer);
		var xSpan, ySpan;
		if (options.useLatLngOrder) {
			ySpan = L.DomUtil.create("span", "", this._inputcontainerWGS84);
			this._inputY = this._createInput("inputY", this._inputcontainerWGS84);
			xSpan = L.DomUtil.create("span", "", this._inputcontainerWGS84);
			this._inputX = this._createInput("inputX", this._inputcontainerWGS84);
		} else {
			xSpan = L.DomUtil.create("span", "", this._inputcontainerWGS84);
			this._inputX = this._createInput("inputX", this._inputcontainerWGS84);
			ySpan = L.DomUtil.create("span", "", this._inputcontainerWGS84);
			this._inputY = this._createInput("inputY", this._inputcontainerWGS84);
		}
		xSpanJTSK = L.DomUtil.create("span", "", this._inputcontainerJTSK);
		this._inputXJTSK = this._createInput("inputX", this._inputcontainerJTSK);
		ySpanJTSK = L.DomUtil.create("span", "", this._inputcontainerJTSK);
		this._inputYJTSK = this._createInput("inputY", this._inputcontainerJTSK);
		xSpan.innerHTML = options.labelTemplateLng.replace("{x}", "");
		ySpan.innerHTML = options.labelTemplateLat.replace("{y}", "");
		xSpanJTSK.innerHTML = "X ";
		ySpanJTSK.innerHTML = "Y ";

		L.DomEvent.on(this._inputX, 'keyup', this._handleKeypress, this);
		L.DomEvent.on(this._inputY, 'keyup', this._handleKeypress, this);
		L.DomEvent.on(this._inputXJTSK, 'keyup', this._handleKeypress, this);
		L.DomEvent.on(this._inputYJTSK, 'keyup', this._handleKeypress, this);
		L.DomEvent.on(container, 'click', function (ev) { //ToDo: zmenit/pridat
			if (ev.target !== this._inputY && ev.target !== this._inputX && ev.target !== this._inputXJTSK && ev.target !== this._inputYJTSK) {
				this.collapse();
			}
		}, this);

		//connect to mouseevents
		map.on("mousemove", this._update, this);
		map.on('dragstart', this.collapse, this);

		map.whenReady(this._update, this);

		this._showsCoordinates = true;
		//wether or not to show inputs on click
		if (options.enableUserInput) {
			L.DomEvent.addListener(this._container, "click", this._switchUI, this);
		}

		return container;
	},

	/**
	 *	Creates an input HTML element in given container with given classname
	 */
	_createInput: function (classname, container) {
		var input = L.DomUtil.create("input", classname, container);
		input.type = "text";
		L.DomEvent.disableClickPropagation(input);
		return input;
	},

	_clearMarker: function () {
		this._map.removeLayer(this._marker);
	},

	/**
	 *	Called onkeyup of input fields
	 */
	_handleKeypress: function (e) {
		switch (e.keyCode) {
			case 27: //Esc
				this.collapse();
				break;
			case 13: //Enter
				this._handleSubmit(e);
				this.collapse();
				break;
			default: //All keys
				this._handleSubmit(e);
				break;
		}
	},

	/**
	 *	Called on each keyup except ESC
	 */
	_handleSubmit: function (e) {
		if (e.target == this._inputY || e.target == this._inputX ) {
			
			var x = L.NumberFormatter.createValidNumber(this._inputX.value, this.options.decimalSeperator);
			var y = L.NumberFormatter.createValidNumber(this._inputY.value, this.options.decimalSeperator);
			if (x !== undefined && y !== undefined) {
				if (this.options.markerType !== null) {
					var marker = this._marker;
					if (!marker) {
						marker = this._marker = this._createNewMarker();
						marker.on("click", this._clearMarker, this);

					}
					var ll = new L.LatLng(y, x);
					marker.setLatLng(ll);
					marker.addTo(this._map);
					if (this.options.centerUserCoordinates) {
						this._map.setView(ll, this._map.getZoom());
					}
				} else {
					this._map.setView([y, x], this._map.getZoom());

				}
			}
		}
		else{
			var x = L.NumberFormatter.createValidNumber(this._inputXJTSK.value, this.options.decimalSeperator);
			var y = L.NumberFormatter.createValidNumber(this._inputYJTSK.value, this.options.decimalSeperator);
			if (x !== undefined && y !== undefined) {
				var latlng= convertToWGS84(x, y);
				if (this.options.markerType !== null) {
					var marker = this._marker;
					if (!marker) {
						marker = this._marker = this._createNewMarker();
						marker.on("click", this._clearMarker, this);

					}
					var ll = new L.LatLng(latlng[1], latlng[0]);
					marker.setLatLng(ll);
					marker.addTo(this._map);
					if (this.options.centerUserCoordinates) {
						this._map.setView(ll, this._map.getZoom());
					}
				} else {
					this._map.setView([latlng[1], latlng[0]], this._map.getZoom());

				}
			}
		}
	},

	/**
	 *	Shows inputs fields
	 */
	expand: function () {
		this._showsCoordinates = false;

		this._map.off("mousemove", this._update, this);

		L.DomEvent.addListener(this._container, "mousemove", L.DomEvent.stop);
		L.DomEvent.removeListener(this._container, "click", this._switchUI, this);

		L.DomUtil.addClass(this._labelcontainer, "uiHidden");
		L.DomUtil.removeClass(this._inputcontainer, "uiHidden");
	},

	/**
	 *	Creates the label according to given options and formatters
	 */
	_createCoordinateLabel: function (ll) {
		var opts = this.options,
			x, y;
		if (opts.customLabelFcn) {
			return opts.customLabelFcn(ll, opts);
		}
		if (opts.labelFormatterLng) {
			x = opts.labelFormatterLng(ll.lng);
		} else {
			x = L.Util.template(opts.labelTemplateLng, {
				x: this._getNumber(ll.lng, opts)
			});
		}
		if (opts.labelFormatterLat) {
			y = opts.labelFormatterLat(ll.lat);
		} else {
			y = L.Util.template(opts.labelTemplateLat, {
				y: this._getNumber(ll.lat, opts)
			});
		}
		if (opts.useLatLngOrder) {
			return y + " " + x;
		}
		return x + " " + y;
	},

	_createCoordinateLabelJTSK: function (ll) {
		var opts = this.options;
		var coords = convertToJTSK(ll.lng, ll.lat, height=0)
		return "X "+L.NumberFormatter.round(coords[0], 2, opts.decimalSeperator) + " Y " + L.NumberFormatter.round(coords[1], 2, opts.decimalSeperator);
	},

	/**
	 *	Returns a Number according to options (DMS or decimal)
	 */
	_getNumber: function (n, opts) {
		var res;
		if (opts.useDMS) {
			res = L.NumberFormatter.toDMS(n);
		} else {
			res = L.NumberFormatter.round(n, opts.decimals, opts.decimalSeperator);
		}
		return res;
	},

	/**
	 *	Shows coordinate labels after user input has ended. Also
	 *	displays a marker with popup at the last input position.
	 */
	collapse: function () {
		if (!this._showsCoordinates) {
			this._map.on("mousemove", this._update, this);
			this._showsCoordinates = true;
			var opts = this.options;
			L.DomEvent.addListener(this._container, "click", this._switchUI, this);
			L.DomEvent.removeListener(this._container, "mousemove", L.DomEvent.stop);

			L.DomUtil.addClass(this._inputcontainer, "uiHidden");
			L.DomUtil.removeClass(this._labelcontainer, "uiHidden");

			if (this._marker) {
				var m = this._createNewMarker(),
					ll = this._marker.getLatLng();
				m.setLatLng(ll);

				var container = L.DomUtil.create("div", "");
				var label = L.DomUtil.create("div", "", container);
				label.innerHTML = this._ordinateLabel(ll);

				var close = L.DomUtil.create("a", "", container);
				close.innerHTML = "Remove";
				close.href = "#";
				var stop = L.DomEvent.stopPropagation;

				L.DomEvent
					.on(close, 'click', stop)
					.on(close, 'mousedown', stop)
					.on(close, 'dblclick', stop)
					.on(close, 'click', L.DomEvent.preventDefault)
					.on(close, 'click', function () {
						this._map.removeLayer(m);
					}, this);

				m.bindPopup(container);
				m.addTo(this._map);
				this._map.removeLayer(this._marker);
				this._marker = null;
			}
		}
	},

	/**
	 *	Click callback for UI
	 */
	_switchUI: function (evt) {
		L.DomEvent.stop(evt);
		L.DomEvent.stopPropagation(evt);
		L.DomEvent.preventDefault(evt);
		if (this._showsCoordinates) {
			//show textfields
			this.expand();
		} else {
			//show coordinates
			this.collapse();
		}
	},

	onRemove: function (map) {
		map.off("mousemove", this._update, this);
	},

	/**
	 *	Mousemove callback function updating labels and input elements
	 */
	_update: function (evt) {
		var pos = evt.latlng,
			opts = this.options;
		if (pos) {
			pos = pos.wrap();
			this._currentPos = pos;
			this._inputY.value = L.NumberFormatter.round(pos.lat, opts.decimals, opts.decimalSeperator);
			this._inputX.value = L.NumberFormatter.round(pos.lng, opts.decimals, opts.decimalSeperator);
			var coords = convertToJTSK(pos.lng, pos.lat, height=0)
			this._inputXJTSK.value = L.NumberFormatter.round(coords[0], 2, opts.decimalSeperator);
			this._inputYJTSK.value = L.NumberFormatter.round(coords[1], 2, opts.decimalSeperator);
			this._label.innerHTML = this._createCoordinateLabel(pos);
			this._labelJTSK.innerHTML = this._createCoordinateLabelJTSK(pos);
		}
	},

	_createNewMarker: function () {
		return this.options.markerType(null, this.options.markerProps);
	}

});

//constructor registration
L.control.coordinates = function (options) {
	return new L.Control.Coordinates(options);
};

//map init hook
L.Map.mergeOptions({
	coordinateControl: false
});

L.Map.addInitHook(function () {
	if (this.options.coordinateControl) {
		this.coordinateControl = new L.Control.Coordinates();
		this.addControl(this.coordinateControl);
	}
});
