from odoo import models, fields, api
import requests

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Location fields
    latitude = fields.Float(string='Latitude', digits=(16, 7), default=0.0)
    longitude = fields.Float(string='Longitude', digits=(16, 7), default=0.0)
    location_name = fields.Char(string='Location Name')
    
    # Device and Network Information
    device_info = fields.Text(string='Device Information')
    ip_address = fields.Char(string='IP Address')
    browser_info = fields.Char(string='Browser Information')
    
    # Mode fields
    check_in_mode = fields.Selection([
        ('manual', 'Manual'),
        ('kiosk', 'Kiosk'),
        ('portal', 'Portal')
    ], string='Check In Mode', default='manual')
    
    check_out_mode = fields.Selection([
        ('manual', 'Manual'),
        ('kiosk', 'Kiosk'),
        ('portal', 'Portal')
    ], string='Check Out Mode', default='manual')
    
    # Additional fields for hours
    extra_hours = fields.Float(string='Extra Hours', compute='_compute_extra_hours', store=True, default=0.0)
    
    @api.depends('worked_hours')
    def _compute_extra_hours(self):
        for attendance in self:
            worked_hours = attendance.worked_hours or 0.0
            attendance.extra_hours = max(0.0, worked_hours - 8.0)  # Assuming 8-hour workday

    def _get_location_name(self, latitude, longitude):
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
            headers = {'User-Agent': 'Odoo HR Attendance GPS'}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                location_data = response.json()
                return location_data.get('display_name', 'Unknown Location')
        except Exception as e:
            _logger.error(f"Error getting location name: {str(e)}")
        return 'Unknown Location'
