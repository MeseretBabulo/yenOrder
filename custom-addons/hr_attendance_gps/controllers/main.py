from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError
class PortalAttendance(http.Controller):
    @http.route('/attendance', 
                type='http', 
                auth='public', 
                methods = ['GET'],
                website=True)
    def portal_attendance(self, **kw):
        _logger.info("KKkkkkkkkkkk")
        employee = request.env.user.employee_id
        _logger.info("employee %s",employee)
        _logger.info("employee %s",employee.name)    
        latitude = kw.get('latitude', False)
        longitude = kw.get('longitude', False)
        location_name = kw.get('location_name', 'Unknown Location')
        
        
        return request.render(
            "attendance_extend.portal_attendance", {}
        )

class HrAttendanceController(http.Controller):
    @http.route('/hr_attendance/check_in', type='json', auth='user')
    def check_in(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            raise ValidationError('No employee linked to your user account')
            
        latitude = kw.get('latitude', False)
        longitude = kw.get('longitude', False)
        location_name = kw.get('location_name', 'Unknown Location')
        
        if not latitude or not longitude:
            raise ValidationError('Location coordinates are required')
            
        attendance = request.env['hr.attendance'].create({
            'employee_id': employee.id,
            'latitude': latitude,
            'longitude': longitude,
            'location_name': location_name,
        })
        return attendance.read()[0]

    @http.route('/hr_attendance/check_out', type='json', auth='user')
    def check_out(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            raise ValidationError('No employee linked to your user account')
            
        latitude = kw.get('latitude', False)
        longitude = kw.get('longitude', False)
        location_name = kw.get('location_name', 'Unknown Location')
        
        if not latitude or not longitude:
            raise ValidationError('Location coordinates are required')
            
        attendance = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)
        
        if attendance:
            attendance.write({
                'check_out': fields.Datetime.now(),
                'latitude': latitude,
                'longitude': longitude,
                'location_name': location_name,
            })
        return attendance.read()[0] if attendance else False