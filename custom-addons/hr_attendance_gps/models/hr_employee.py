from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def attendance_manual(self, vals):
        """Override to include GPS coordinates"""
        if not vals.get('latitude') or not vals.get('longitude'):
            raise ValidationError('Location coordinates are required for attendance')

        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_out', '=', False),
        ], limit=1)

        if attendance:  # Check OUT
            attendance.write({
                'check_out': fields.Datetime.now(),
                'latitude': vals.get('latitude', 0.0),
                'longitude': vals.get('longitude', 0.0),
            })
        else:  # Check IN
            self.env['hr.attendance'].create({
                'employee_id': self.id,
                'check_in': fields.Datetime.now(),
                'latitude': vals.get('latitude', 0.0),
                'longitude': vals.get('longitude', 0.0),
            })

        return self.env['ir.actions.act_window'].for_xml_id('hr_attendance', 'hr_attendance_action_my_attendances') 