from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def attendance_scan_with_location(self, barcode, latitude, longitude):
        employee = self.search([('barcode', '=', barcode)], limit=1)
        if employee:
            return employee._attendance_action_change_with_location(latitude, longitude)
        return False

    @api.model
    def attendance_manual_with_location(self, employee_id, latitude, longitude):
        employee = self.browse(employee_id)
        return employee._attendance_action_change_with_location(latitude, longitude)

    def _attendance_action_change_with_location(self, latitude, longitude):
        self.ensure_one()
        action_date = fields.Datetime.now()
        
        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
                'latitude': latitude,
                'longitude': longitude,
            }
        else:
            vals = {
                'check_out': action_date,
                'latitude': latitude,
                'longitude': longitude,
            }
            attendance = self.env['hr.attendance'].search(
                [('employee_id', '=', self.id), ('check_out', '=', False)], 
                limit=1
            )
            if attendance:
                attendance.write(vals)
                return attendance

        try:
            # Get location name using reverse geocoding
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
            headers = {'User-Agent': 'Odoo HR Attendance GPS'}
            response = requests.get(url, headers=headers)
            location_data = response.json()
            vals['location_name'] = location_data.get('display_name', 'Unknown Location')
        except Exception as e:
            _logger.error(f"Error getting location name: {str(e)}")
            vals['location_name'] = f"({latitude}, {longitude})"

        attendance = self.env['hr.attendance'].create(vals)
        return attendance

    @api.model
    def attendance_manual_check_in(self, location_data=None):
        res = super().attendance_manual_check_in()
        if location_data and res:
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', self.id),
                ('check_out', '=', False)
            ], limit=1)
            if attendance:
                attendance.write({
                    'latitude': location_data.get('latitude'),
                    'longitude': location_data.get('longitude'),
                    'location_name': location_data.get('location_name', 'Unknown')
                })
        return res

    @api.model
    def attendance_manual_check_out(self, location_data=None):
        res = super().attendance_manual_check_out()
        if location_data and res:
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', self.id),
                ('check_out', '!=', False)
            ], order='check_out desc', limit=1)
            if attendance:
                attendance.write({
                    'latitude': location_data.get('latitude'),
                    'longitude': location_data.get('longitude'),
                    'location_name': location_data.get('location_name', 'Unknown')
                })
        return res


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    latitude = fields.Float(string='Latitude', digits=(16, 7))
    longitude = fields.Float(string='Longitude', digits=(16, 7))
    location_name = fields.Char(string='Location Name')