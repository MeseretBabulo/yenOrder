odoo.define('portal_attendance.attendance_map', [
    'web.FormRenderer',
    'web.FormView',
    'web.view_registry'
], function (require) {
    'use strict';

    var FormRenderer = require('web.FormRenderer');
    var FormView = require('web.FormView');
    var viewRegistry = require('web.view_registry');

    var AttendanceFormRenderer = FormRenderer.extend({
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initMap();
            });
        },

        _initMap: function () {
            var self = this;
            var record = this.state.data;

            if (record.latitude && record.longitude) {
                var mapElement = this.el.querySelector('#attendance_map');
                if (mapElement) {
                    // Clear any existing map
                    mapElement.innerHTML = '';

                    // Initialize the map
                    var map = L.map(mapElement).setView([record.latitude, record.longitude], 13);

                    // Add OpenStreetMap tiles
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '© OpenStreetMap contributors'
                    }).addTo(map);

                    // Add a marker for the attendance location
                    var marker = L.marker([record.latitude, record.longitude]).addTo(map);

                    // Add a popup with location information
                    var popupContent = '<b>' + (record.location_name || 'Location') + '</b><br>' +
                        'Latitude: ' + record.latitude + '<br>' +
                        'Longitude: ' + record.longitude;

                    if (record.check_in) {
                        popupContent += '<br>Check-in: ' + moment(record.check_in).format('YYYY-MM-DD HH:mm:ss');
                    }
                    if (record.check_out) {
                        popupContent += '<br>Check-out: ' + moment(record.check_out).format('YYYY-MM-DD HH:mm:ss');
                    }

                    marker.bindPopup(popupContent).openPopup();

                    // Fix map display issues
                    setTimeout(function () {
                        map.invalidateSize();
                    }, 0);
                }
            }
        },
    });

    var AttendanceFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Renderer: AttendanceFormRenderer,
        }),
    });

    viewRegistry.add('attendance_form_with_map', AttendanceFormView);

    return {
        AttendanceFormRenderer: AttendanceFormRenderer,
        AttendanceFormView: AttendanceFormView,
    };
}); 