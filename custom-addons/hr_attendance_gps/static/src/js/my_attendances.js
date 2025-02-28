/** @odoo-module **/

import { MyAttendances } from '@hr_attendance/js/my_attendances';
import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';

patch(MyAttendances.prototype, {
    setup() {
        this._super(...arguments);
    },

    // Override the original attendance button click handler
    async onClickAttendanceButton() {
        try {
            // Check for geolocation support
            if (!navigator.geolocation) {
                throw new Error('Geolocation is not supported by your browser');
            }

            // Show confirmation dialog based on check-in/out state
            const action = this.employee.attendance_state === 'checked_in' ? 'check out' : 'check in';
            const confirmed = await this.env.services.dialog.confirm(
                _t('Location Update Required'),
                _t(`Are you sure you want to ${action}? Your current location will be recorded.`),
                {
                    confirm_text: this.employee.attendance_state === 'checked_in' ? _t('Goodbye') : _t('OK'),
                    cancel_text: _t('Cancel')
                }
            );

            if (!confirmed) {
                return false;
            }

            // Try to get location first
            const position = await this._getCurrentPosition();

            // Validate coordinates
            if (!this._isValidCoordinate(position.coords.latitude) ||
                !this._isValidCoordinate(position.coords.longitude)) {
                throw new Error('Invalid coordinates received');
            }

            // Get location details
            const locationData = await this._getLocationDetails(position.coords.latitude, position.coords.longitude);

            // If we got here, we have valid location data, proceed with attendance
            const attendanceData = {
                employee_id: this.employee.id,
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                location_name: locationData.display_name || 'Unknown'
            };

            // Call the original attendance method with the location data
            if (this.employee.attendance_state === 'checked_in') {
                await this.model.checkOut(attendanceData);
            } else {
                await this.model.checkIn(attendanceData);
            }

            // Show success message
            this.env.services.notification.notify({
                title: _t('Success'),
                message: _t(`Location recorded: ${locationData.display_name}`),
                type: 'success',
            });

            // Refresh the view
            this.action.doAction('hr_attendance.hr_attendance_action_my_attendances');

        } catch (error) {
            console.error('Location error:', error);

            let errorMessage;
            if (error.code === 1) { // PERMISSION_DENIED
                errorMessage = _t('Location access is required for attendance. Please:\n\n' +
                    '1. Click the location icon in your browser\'s address bar\n' +
                    '2. Select "Allow" for location access\n' +
                    '3. Try checking in/out again');
            } else if (error.code === 2) { // POSITION_UNAVAILABLE
                errorMessage = _t('Unable to get your location. Please check your device\'s GPS settings.');
            } else if (error.code === 3) { // TIMEOUT
                errorMessage = _t('Location request timed out. Please try again.');
            } else {
                errorMessage = _t('Please enable location services to check in/out.');
            }

            this.env.services.notification.notify({
                title: _t('Location Required'),
                message: errorMessage,
                type: 'danger',
                sticky: true,
            });
            return false;
        }
    },

    _isValidCoordinate(coord) {
        return typeof coord === 'number' && !isNaN(coord) && coord !== 0;
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
            throw new Error('Failed to get location details');
        }
    }
});