/** @odoo-module **/

import { PublicKioskApp } from "@hr_attendance/public_kiosk/public_kiosk_app";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PublicKioskApp.prototype, {
    setup() {
        this._super(...arguments);
        // Store original methods
        this._originalHandleEmployeeBarcode = this.handleEmployeeBarcode;
        this._originalHandleEmployeeClick = this.handleEmployeeClick;
        // Override with GPS-enabled versions
        this.handleEmployeeBarcode = this._handleEmployeeBarcodeWithGPS;
        this.handleEmployeeClick = this._handleEmployeeClickWithGPS;
    },

    async _handleEmployeeClickWithGPS(ev) {
        try {
            // Check for geolocation support
            if (!navigator.geolocation) {
                throw new Error('Geolocation is not supported by your browser');
            }

            // Get current position
            const position = await this._getCurrentPosition();

            // Get location details
            const locationData = await this._getLocationDetails(
                position.coords.latitude,
                position.coords.longitude
            );

            // Store location data
            this.locationData = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                location_name: locationData.display_name || 'Unknown'
            };

            // Call original click handler
            return this._originalHandleEmployeeClick(ev);

        } catch (error) {
            console.error('Location error:', error);
            this.env.services.notification.notify({
                title: _t('Location Required'),
                message: _t('Please enable location services to check in/out.'),
                type: 'danger',
                sticky: true,
            });
            return false;
        }
    },

    async handleEmployeeAction(employee) {
        try {
            if (!this.locationData) {
                // Get location if not already obtained
                const position = await this._getCurrentPosition();
                const locationData = await this._getLocationDetails(
                    position.coords.latitude,
                    position.coords.longitude
                );
                this.locationData = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    location_name: locationData.display_name || 'Unknown'
                };
            }

            // Add location data to the attendance action
            const action = employee.attendance_state === 'checked_in' ? 'attendance_manual_check_out' : 'attendance_manual_check_in';

            // Call the server with location data
            await this.orm.call('hr.employee', action, [[employee.id]], {
                location_data: this.locationData
            });

            // Show success message with location
            this.env.services.notification.notify({
                title: _t('Success'),
                message: _t(`Location recorded: ${this.locationData.location_name}`),
                type: 'success',
            });

            // Clear location data after use
            this.locationData = null;

            // Update the state
            await this.updateState();

        } catch (error) {
            console.error('Error in handleEmployeeAction:', error);
            this.env.services.notification.notify({
                title: _t('Error'),
                message: error.message || _t('An error occurred during the attendance action.'),
                type: 'danger',
            });
        }
    },

    async _getCurrentPosition() {
        return new Promise((resolve, reject) => {
            const options = {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            };

            navigator.geolocation.getCurrentPosition(
                (position) => resolve(position),
                (error) => reject(error),
                options
            );
        });
    },

    async _getLocationDetails(latitude, longitude) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`,
                {
                    headers: {
                        'Accept': 'application/json',
                        'User-Agent': 'Odoo HR Attendance GPS'
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to fetch location details');
            }

            const data = await response.json();
            return {
                display_name: data.display_name,
                address: data.address
            };
        } catch (error) {
            console.error('Error fetching location details:', error);
            return { display_name: 'Unknown' };
        }
    },

    async kioskReturn() {
        // Store the original kioskReturn method
        const originalKioskReturn = this.props.kioskReturn;

        try {
            // Check for geolocation support
            if (!navigator.geolocation) {
                throw new Error('Geolocation is not supported by your browser');
            }

            // Get current position
            const position = await this._getCurrentPosition();

            // Get location details
            const locationData = await this._getLocationDetails(
                position.coords.latitude,
                position.coords.longitude
            );

            // Store location data with the attendance
            if (this.attendance) {
                await this.orm.write('hr.attendance', [this.attendance.id], {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    location_name: locationData.display_name || 'Unknown'
                });

                // Show success message
                this.env.services.notification.notify({
                    title: _t('Success'),
                    message: _t(`Location recorded: ${locationData.display_name}`),
                    type: 'success',
                });
            }

            // Call the original kioskReturn function
            if (originalKioskReturn) {
                originalKioskReturn();
            }

        } catch (error) {
            console.error('Location error:', error);

            let errorMessage;
            if (error.code === 1) { // PERMISSION_DENIED
                errorMessage = _t('Location access is required. Please enable location services and try again.');
            } else if (error.code === 2) { // POSITION_UNAVAILABLE
                errorMessage = _t('Unable to get your location. Please check your GPS settings.');
            } else if (error.code === 3) { // TIMEOUT
                errorMessage = _t('Location request timed out. Please try again.');
            } else {
                errorMessage = _t('Please enable location services to continue.');
            }

            this.env.services.notification.notify({
                title: _t('Location Required'),
                message: errorMessage,
                type: 'danger',
                sticky: true,
            });
        }
    }
}); 