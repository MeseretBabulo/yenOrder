
/** @odoo-module **/
console.log("loaded2....");

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useRef, useState,onMounted } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class LocationLatLngCA extends Component {
    static template = 'bista_timesheet_attendance.LocationLatLngCA';
    static props = {
        ...standardFieldProps,
        string: { type: String, optional: true },
        classList: { type: String, optional: true },
        style: { type: String, optional: true },
        showMap: { type: Boolean, optional: true },
        mapHeight: { type: String, optional: true },
        mapWidth: { type: String, optional: true },
        buttonAttrs: { type: Object, optional: true },
        latField: { type: String },
        lngField: { type: String },
    };
    static defaultProps = {
        string: _t('Get Location'),
        mapHeight: '450',
        mapWidth: '100%',
        showMap: false,
    };

    setup() {
        this.orm = useService('orm');
        this.mapContainerRef = useRef('mapContainer');
        this.state = useState({
            latitude: this.props.record.data[this.props.latField],
            longitude: this.props.record.data[this.props.lngField],
            showMap: false,
        });

        onMounted(() => {
            this._initializeMap();
        });
    }

    _initializeMap() {
        if (this.props.showMap) {
            const latitude = this.props.record.data[this.props.latField];
            const longitude = this.props.record.data[this.props.lngField];

            this.state.latitude = latitude;
            this.state.longitude = longitude;
            this.state.showMap = true;
        }
    }
    async _onClickGetLocation() {
        console.log("_onClickGetLocation--");
    
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by this browser.');
            return;
        }
    
        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true, // More precise location
                    timeout: 10000, // Wait up to 10s
                    maximumAge: 0, // Do not use cached locations
                });
            });
    
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
    
            console.log("Latitude:", lat);
            console.log("Longitude:", lng);
    
            if (this.props.buttonAttrs) {
                await this._callButton(lat, lng);
            // } else {
            //     await this.props.record.update({
            //         [this.props.latField]: lat,
            //         [this.props.lngField]: lng,
            //     });
    
            //     this.state.latitude = lat;
            //     this.state.longitude = lng;
            //     this.state.showMap = true;
            //     this._initializeMap();
            }
        } catch (error) {
            console.error('Error getting location:', error);
            if (error.code === 1) {
                alert('Permission denied. Please allow location access.');
            } else if (error.code === 2) {
                alert('Position unavailable. Try again later.');
            } else if (error.code === 3) {
                alert('Location request timed out. Please try again.');
            } else {
                alert('An unknown error occurred.');
            }
        }
    }
    
    async _callButton(lat, lng) {
        console.log("_callButton----JJJ--");
        if (!this.props.buttonAttrs) {
            return;
        }
    
        await this.orm.call(
            'project.task',
            this.props.buttonAttrs.name,
            [this.props.buttonAttrs,this.props.record.resId, lat, lng], // Pass resId, lat, and lng as positional arguments
            {
                context: this.props.record.context,
                mode: this.props.readonly ? 'readonly' : 'edit',
            }
        );
    }
}
export const locationLatLngCA = {
    component: LocationLatLngCA,
    supportedTypes: ['float'],
    extractProps: ({ attrs }) => ({
        string: attrs.string,
        classList: attrs.classList,
        style: attrs.style,
        showMap: !!(attrs.show_map == 'true'),
        mapHeight: attrs.map_height || '450',
        mapWidth: attrs.map_width || '100%',
        buttonAttrs: attrs.button_attrs ? JSON.parse(attrs.button_attrs) : false,
        latField: attrs.lat,
        lngField: attrs.lng,
    }),
};

registry.category("view_widgets").add("location_lat_lng", locationLatLngCA);
